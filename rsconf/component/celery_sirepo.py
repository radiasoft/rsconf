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
        from rsconf.component import docker_registry

        self.buildt.require_component('docker')
        j2_ctx = self.hdb.j2_ctx_copy()
        systemd.docker_unit_prepare(self, j2_ctx)
        env = pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=self.hdb.rsconf_db.channel,
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
        )
        for f in (
            'sirepo.celery_tasks.broker_url',
            'sirepo.mpi_cores',
            'sirepo.celery_tasks.celeryd_concurrency',
        ):
            env[f.upper().replace('.', '_')] = j2_ctx.nested_get(f)
        # Might be on a different server so need to setup permissions right
        user_d = sirepo.install_user_d(self, j2_ctx)
        #TODO(robnagler) need to set hostname so celery flower shows up right
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            image=docker_registry.absolute_image(j2_ctx, j2_ctx.sirepo.docker_image),
            cmd="celery worker --app=sirepo.celery_tasks --no-color -Ofair '--queue={}'".format(j2_ctx.celery_sirepo.queues),
            env=env,
            volumes=[user_d],
            after=['rabbitmq.service'],
        )
