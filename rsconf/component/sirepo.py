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


_DB_SUBDIR = 'db'
#TODO(robnagler) import from sirepo directly
_USER_SUBDIR = 'user'
_BEAKER_SECRET_BASE = 'sirepo_beaker_secret'


def user_d(j2_ctx):
    return systemd.docker_unit_run_d(j2_ctx, 'sirepo').join(_DB_SUBDIR, _USER_SUBDIR)


class T(component.T):
    def internal_build(self):
        from rsconf.component import nginx
        from rsconf.component import docker_registry

        self.buildt.require_component('docker', 'nginx')
        j2_ctx = self.hdb.j2_ctx_copy()
        run_d = systemd.docker_unit_prepare(self)
        db_d = run_d.join(_DB_SUBDIR)
        #TODO(robnagler) from sirepo or flask(?)
        beaker_secret_f = db_d.join('beaker_secret')
        env = pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=j2_ctx.rsconf_db.channel,
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
            SIREPO_PKCLI_SERVICE_IP='0.0.0.0',
            SIREPO_PKCLI_SERVICE_RUN_DIR=run_d,
            SIREPO_SERVER_BEAKER_SESSION_KEY='sirepo_{}'.format(j2_ctx.rsconf_db.channel),
            SIREPO_SERVER_BEAKER_SESSION_SECRET=beaker_secret_f,
            SIREPO_SERVER_DB_DIR=db_d,
            SIREPO_SERVER_JOB_QUEUE='Celery',
        )
        for f in (
            'sirepo.celery_tasks.broker_url',
            'sirepo.pkcli.service_port',
            'sirepo.pkcli.service_processes',
            'sirepo.pkcli.service_threads',
            'sirepo.oauth.github_key',
            'sirepo.oauth.github_secret',
            'sirepo.server.oauth_login',
        ):
            env[f.upper().replace('.', '_')] = _env_value(j2_ctx.nested_get(f))
        systemd.docker_unit_enable(
            self,
            image=docker_registry.absolute_image(j2_ctx, j2_ctx.sirepo.docker_image),
            env=env,
            cmd='sirepo service uwsgi',
            after=['celery_sirepo.service'],
            #TODO(robnagler) wanted by nginx
        )
        self.install_access(mode='700', owner=j2_ctx.rsconf_db.run_u)
        self.install_directory(db_d)
        self.install_directory(user_d(j2_ctx))
        self.install_secret_path(
            _BEAKER_SECRET_BASE,
            host_path=beaker_secret_f,
            gen_secret=lambda p: db.random_string(path=p, length=64),
        )
        nginx.install_vhost(self, vhost=j2_ctx.sirepo.vhost, j2_ctx=j2_ctx)

    def _gen_beaker_secret(self, tgt):
        from rsconf.pkcli import sirepo

        sirepo.gen_beaker_secret(tgt)


#TODO(robnagler) pkconfig needs to handle False, True, etc.
def _env_value(v):
    if isinstance(v, bool):
        return '1' if v else ''
    return str(v)
