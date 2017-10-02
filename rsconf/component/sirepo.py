# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from rsconf import systemd
from pykern import pkcollections

_DB_SUBDIR = 'db'
#TODO(robnagler) import from sirepo directly
_USER_SUBDIR = 'user'
_BEAKER_SECRET_BASE = 'sirepo_beaker_secret'

def user_d(hdb):
    return systemd.docker_unit_run_d(hdb, 'sirepo').join(_DB_SUBDIR, _USER_SUBDIR)


class T(component.T):
    def internal_build(self):
        from rsconf.component import nginx

        self.buildt.require_component('celery_sirepo', 'nginx')
        run_d = systemd.docker_unit_prepare(self)
        db_d = run_d.join(_DB_SUBDIR)
        #TODO(robnagler) from sirepo or flask(?)
        beaker_secret_f = db_d.join('beaker_secret')
        env = pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=self.hdb.rsconf_db_channel,
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
            SIREPO_PKCLI_SERVICE_IP='0.0.0.0',
            SIREPO_PKCLI_SERVICE_RUN_DIR=run_d,
            SIREPO_SERVER_BEAKER_SESSION_KEY='sirepo_{}'.format(self.hdb.rsconf_db_channel),
            SIREPO_SERVER_BEAKER_SESSION_SECRET=beaker_secret_f,
            SIREPO_SERVER_DB_DIR=db_d,
            SIREPO_SERVER_JOB_QUEUE='Celery',
        )
        for f in (
            'sirepo_celery_tasks_broker_url',
            'sirepo_pkcli_service_port',
            'sirepo_pkcli_service_processes',
            'sirepo_pkcli_service_threads',
            'sirepo_oauth_github_key',
            'sirepo_oauth_github_secret',
            'sirepo_server_oauth_login',
        ):
            env[f.upper()] = _env_value(self.hdb[f])
        systemd.docker_unit_enable(
            self,
            image='radiasoft/sirepo',
            env=env,
            cmd='sirepo service uwsgi',
            after=['celery_sirepo.service'],
            #TODO(robnagler) wanted by nginx
        )
        self.install_access(mode='700', owner=self.hdb.rsconf_db_run_u)
        self.install_directory(db_d)
        self.install_directory(user_d(self.hdb))
        self.install_secret(
            _BEAKER_SECRET_BASE,
            host_path=beaker_secret_f,
            gen_secret=self._gen_beaker_secret,
        )
        nginx.install_vhost(self)

    def _gen_beaker_secret(self, tgt):
        from rsconf.pkcli import sirepo

        sirepo.gen_beaker_secret(tgt)


#TODO(robnagler) pkconfig needs to handle False, True, etc.
def _env_value(v):
    if isinstance(v, bool):
        return '1' if v else ''
    return str(v)
