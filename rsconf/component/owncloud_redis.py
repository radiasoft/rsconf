# -*- coding: utf-8 -*-
u"""create owncloud_redis config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
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
        z = j2_ctx.owncloud_redis
        z.run_u = j2_ctx.rsconf_db.root_u
        z.run_d = systemd.docker_unit_prepare(self, j2_ctx)
        self.install_access(mode='700', owner=z.run_u)
        z.conf_f = z.run_d.join('redis.conf')
        z.db_d = z.run_d.join('db')
        self.install_directory(z.db_d)
        self.install_access(mode='400')
        self.install_resource('owncloud_redis/redis.conf', j2_ctx, z.conf_f)
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            cmd="/usr/bin/redis-server '{}'".format(z.conf_f),
        )
