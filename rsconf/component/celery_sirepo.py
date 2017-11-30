# -*- coding: utf-8 -*-
u"""create celery sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import sirepo

        self.buildt.require_component('docker', 'rabbitmq')
        systemd.docker_unit_prepare(self)
        env = pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=self.hdb.rsconf_db_channel,
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
        )
        for f in (
            'sirepo_celery_tasks_broker_url',
            'sirepo_mpi_cores',
            'sirepo_celery_tasks_celeryd_concurrency',
        ):
            env[f.upper()] = self.hdb[f]
        #TODO(robnagler) need to set hostname so celery flower shows up right
        systemd.docker_unit_enable(
            self,
            image='docker.io/radiasoft/sirepo',
            cmd="celery worker --app=sirepo.celery_tasks --no-color -Ofair '--queue={}'".format(self.hdb.celery_sirepo_queues),
            env=env,
            volumes=[sirepo.user_d(self.hdb)],
            after=['rabbitmq.service'],
        )
