# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig
from rsconf import component
from rsconf import db
from rsconf import systemd
import base64
import os


_DB_SUBDIR = 'db'
#TODO(robnagler) import from sirepo directly
_USER_SUBDIR = 'user'
_BEAKER_SECRET_BASE = 'sirepo_beaker_secret'
_COOKIE_PRIVATE_KEY = 'sirepo_cookie_private_key'


def install_user_d(compt, j2_ctx):
    run_d = systemd.unit_run_d(j2_ctx, 'sirepo')
    compt.install_access(mode='700', owner=j2_ctx.rsconf_db.run_u)
    compt.install_directory(run_d)
    db_d = run_d.join(_DB_SUBDIR)
    compt.install_directory(db_d)
    user_d = db_d.join(_USER_SUBDIR)
    compt.install_directory(user_d)
    return user_d


class T(component.T):
    def internal_build(self):
        from rsconf.component import db_bkp
        from rsconf.component import nginx
        from rsconf.component import docker_registry
        from rsconf.component import docker

        self.buildt.require_component('docker', 'nginx', 'db_bkp')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.sirepo
        run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.db_d = run_d.join(_DB_SUBDIR)
        z.run_u = j2_ctx.rsconf_db.run_u
        beaker_secret_f = z.db_d.join('beaker_secret')
        cookie_name = 'sirepo_{}'.format(j2_ctx.rsconf_db.channel)
        docker_hosts = z.get('docker_hosts')
        env = pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=j2_ctx.rsconf_db.channel,
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
            SIREPO_BEAKER_COMPAT_KEY=cookie_name,
            SIREPO_BEAKER_COMPAT_SECRET=beaker_secret_f,
            SIREPO_COOKIE_HTTP_NAME=cookie_name,
            SIREPO_PKCLI_SERVICE_IP='0.0.0.0',
            SIREPO_PKCLI_SERVICE_RUN_DIR=run_d,
            SIREPO_RUNNER_JOB_CLASS='Docker' if docker_hosts else 'Celery',
            SIREPO_RUNNER_DOCKER_IMAGE=docker_registry.absolute_image(j2_ctx, z.docker_image),
            SIREPO_SERVER_DB_DIR=z.db_d,
        )
        env.SIREPO_COOKIE_PRIVATE_KEY = self.secret_path_value(
            _COOKIE_PRIVATE_KEY,
            gen_secret=lambda: base64.urlsafe_b64encode(os.urandom(32)),
            visibility='channel',
        )[0]
        params = [
            'sirepo.oauth.github_key',
            'sirepo.oauth.github_secret',
            'sirepo.pkcli.service_port',
            'sirepo.pkcli.service_processes',
            'sirepo.pkcli.service_threads',
        ]
        if docker_hosts:
            docker_tls_d = run_d.join('docker_tls')
            env.SIREPO_RUNNER_DOCKER_HOSTS = pkconfig.TUPLE_SEP.join(docker_hosts)
            env.SIREPO_RUNNER_DOCKER_TLS_DIR = docker_tls_d
            params.append('sirepo.mpi_cores')
        else:
            params.append('sirepo.celery_tasks.broker_url')
        for f in params:
            env[f.upper().replace('.', '_')] = _env_value(j2_ctx.nested_get(f))
        oauth = bool(env.SIREPO_OAUTH_GITHUB_SECRET)
        if oauth:
            env.SIREPO_FEATURE_CONFIG_API_MODULES = 'oauth'
        #TODO(robnagler) remove once new cookies are on prod
        env.SIREPO_SERVER_BEAKER_SESSION_KEY = env.SIREPO_BEAKER_COMPAT_KEY
        env.SIREPO_SERVER_BEAKER_SESSION_SECRET = env.SIREPO_BEAKER_COMPAT_SECRET
        env.SIREPO_SERVER_OAUTH_LOGIN = _env_value(oauth)
        #TODO(robnagler) removed when docker on prod
        env.SIREPO_SERVER_JOB_QUEUE = env.SIREPO_RUNNER_JOB_CLASS
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            env=env,
            cmd='sirepo service uwsgi',
            after=[] if docker_hosts else ['celery_sirepo.service'],
            #TODO(robnagler) wanted by nginx
        )
        install_user_d(self, j2_ctx)
        self.install_access(mode='400')
        self.install_secret_path(
            _BEAKER_SECRET_BASE,
            host_path=beaker_secret_f,
            gen_secret=lambda: db.random_string(length=64),
        )
        nginx.install_vhost(
            self,
            vhost=z.vhost,
            backend_host=j2_ctx.rsconf_db.host,
            backend_port=z.pkcli.service_port,
            j2_ctx=j2_ctx,
        )
        db_bkp.install_script_and_subdir(
            self,
            j2_ctx,
            run_u=z.run_u,
            run_d=run_d,
        )
        if docker_hosts:
            docker.setup_cluster(
                self,
                docker_hosts,
                docker_tls_d,
                run_u=z.run_u,
                j2_ctx=j2_ctx,
            )


def _env_value(v):
    return str(v)
