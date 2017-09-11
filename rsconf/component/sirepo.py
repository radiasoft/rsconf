# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

_DB_SUBDIR = 'db'
_BEAKER_SECRET_BASE = 'sirepo_beaker_secret'

class T(component.T):
    def internal_build(self):
        from rsconf import systemd

        self.buildt.require_component('docker')
        #self.buildt.require_component('docker', 'rabbitmq', 'celery_sirepo', 'nginx')
        run_d = systemd.docker_unit_prepare(self)
        db_d = run_d.join(_DB_SUBDIR)
        #TODO(robnagler) from sirepo or flask(?)
        beaker_secret_f = db_d.join('beaker_secret')
        env = pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=self.hdb.channel,
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
            SIREPO_PKCLI_SERVICE_IP='0.0.0.0',
            SIREPO_PKCLI_SERVICE_RUN_DIR=run_d,
            SIREPO_SERVER_BEAKER_SESSION_KEY='sirepo_{}'.format(self.hdb.channel),
            SIREPO_SERVER_BEAKER_SESSION_SECRET=beaker_secret_f,
            SIREPO_SERVER_DB_DIR=db_d,
            SIREPO_SERVER_JOB_QUEUE='Celery',
        )
        for f in (
            'sirepo_celery_tasks_broker_url',
            'sirepo_mpi_cores',
            'sirepo_pkcli_service_port',
            'sirepo_pkcli_service_processes',
            'sirepo_pkcli_service_threads',
            'sirepo_oauth_github_key',
            'sirepo_oauth_github_secret',
            'sirepo_server_oauth_login',
        ):
            env[f.upper()] = self.hdb[f]
        systemd.docker_unit(
            self,
            image='radiasoft/sirepo',
            env=env,
            after=['celery_sirepo.service'],
            #TODO(robnagler) wanted by nginx
        )
        self.install_access(mode='700', owner=self.hdb.run_u)
        self.install_directory(db_d)
        #TODO(robnagler) import from sirepo directly
        self.install_directory(db_d.join('user'))
        self.install_secret(
            _BEAKER_SECRET_BASE,
            host_path=beaker_secret_f,
            gen_secret=self._gen_beaker_secret,
        )

    def _gen_beaker_secret(self, tgt):
        from rsconf.pkcli import sirepo

        sirepo.gen_beaker_secret(tgt)


#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly
#TODO(robnagler) only reload if a change, restart if a change
