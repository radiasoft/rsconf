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

        self.buildt.require_component('docker')
        run_d = systemd.docker_unit_prepare(self)
        env = pkcollections.Dict(
            HOME=run_d,
            RABBITMQ_CONFIG_FILE=run_d.join('rabbitmq'),
            RABBITMQ_HOME=run_d,
            RABBITMQ_LOG_BASE=run_d.join('log'),
            RABBITMQ_MNESIA_BASE=run_d.join('mnesia'),
        )
        systemd.docker_unit_enable(
            self,
            image='docker.io/radiasoft/rabbitmq',
            env=env,
            cmd='/usr/lib/rabbitmq/bin/rabbitmq-server',
            after=['docker.service'],
        )
        self.install_access(mode='700', owner=self.hdb.rsconf_db_run_u)
        self.install_directory(env.RABBITMQ_LOG_BASE)
        self.install_directory(env.RABBITMQ_MNESIA_BASE)
        for f in ('enabled_plugins', 'rabbitmq.config'):
            self.install_resource('rabbitmq/' + f, {}, run_d.join(f))
