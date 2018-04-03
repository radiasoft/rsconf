# -*- coding: utf-8 -*-
u"""create rabbitmq configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        self.buildt.require_component('docker')
        j2_ctx = self.hdb.j2_ctx_copy()
        run_d = systemd.docker_unit_prepare(self, j2_ctx)
        env = pkcollections.Dict(
            HOME=run_d,
            RABBITMQ_CONFIG_FILE=run_d.join('rabbitmq'),
            RABBITMQ_HOME=run_d,
            RABBITMQ_LOG_BASE=run_d.join('log'),
            RABBITMQ_MNESIA_BASE=run_d.join('mnesia'),
        )
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            image=docker_registry.absolute_image(j2_ctx, j2_ctx.rabbitmq.docker_image),
            env=env,
            cmd='/usr/lib/rabbitmq/bin/rabbitmq-server',
        )
        self.install_access(mode='700', owner=j2_ctx.rsconf_db.run_u)
        self.install_directory(env.RABBITMQ_LOG_BASE)
        self.install_directory(env.RABBITMQ_MNESIA_BASE)
        for f in ('enabled_plugins', 'rabbitmq.config'):
            self.install_resource('rabbitmq/' + f, j2_ctx, run_d.join(f))
