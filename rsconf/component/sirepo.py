# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
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

        self.buildt.require_component('docker', 'nginx', 'db_bkp')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.sirepo
        run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.db_d = run_d.join(_DB_SUBDIR)
        #TODO(robnagler) from sirepo or flask(?)
        beaker_secret_f = z.db_d.join('beaker_secret')
        cookie_name = 'sirepo_{}'.format(j2_ctx.rsconf_db.channel)
        env = pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=j2_ctx.rsconf_db.channel,
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
            SIREPO_PKCLI_SERVICE_IP='0.0.0.0',
            SIREPO_PKCLI_SERVICE_RUN_DIR=run_d,
            SIREPO_BEAKER_COMPAT_KEY=cookie_name,
            SIREPO_BEAKER_COMPAT_SECRET=beaker_secret_f,
            SIREPO_COOKIE_HTTP_NAME=cookie_name,
            SIREPO_SERVER_DB_DIR=z.db_d,
            SIREPO_SERVER_JOB_QUEUE='Celery',
        )
        env.SIREPO_COOKIE_PRIVATE_KEY = self.secret_path_value(
            _COOKIE_PRIVATE_KEY,
            gen_secret=lambda: base64.urlsafe_b64encode(os.urandom(32)),
            visibility='channel',
        )[0]
        for f in (
            'sirepo.celery_tasks.broker_url',
            'sirepo.oauth.github_key',
            'sirepo.oauth.github_secret',
            'sirepo.pkcli.service_port',
            'sirepo.pkcli.service_processes',
            'sirepo.pkcli.service_threads',
        ):
            env[f.upper().replace('.', '_')] = _env_value(j2_ctx.nested_get(f))
        oauth = bool(env.SIREPO_OAUTH_GITHUB_SECRET)
        if oauth:
            env.SIREPO_FEATURE_CONFIG_API_MODULES = 'oauth'
        #TODO(robnagler) remove once new cookies are on prod
        env.SIREPO_SERVER_BEAKER_SESSION_KEY = env.SIREPO_BEAKER_COMPAT_KEY
        env.SIREPO_SERVER_BEAKER_SESSION_SECRET = env.SIREPO_BEAKER_COMPAT_SECRET
        env.SIREPO_SERVER_OAUTH_LOGIN = _env_value(oauth)
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            env=env,
            cmd='sirepo service uwsgi',
            after=['celery_sirepo.service'],
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
            run_u=j2_ctx.rsconf_db.run_u,
            run_d=run_d,
        )


#TODO(robnagler) pkconfig needs to handle False, True, etc.
def _env_value(v):
    if isinstance(v, bool):
        return '1' if v else ''
    return str(v)
