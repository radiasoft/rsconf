# -*- coding: utf-8 -*-
u"""create spamassassin spamd configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio


class T(component.T):

    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker_registry
        from rsconf.component import network

        # https://github.com/dinkel/docker-spamassassin/blob/master/Dockerfile
        self.buildt.require_component('docker')
        j2_ctx = self.hdb.j2_ctx_copy()
        network.update_j2_ctx(j2_ctx)
        run_d = systemd.docker_unit_prepare(self)
        run = run_d.join('run')
        systemd.docker_unit_enable(
            self,
            image=docker_registry.absolute_image(j2_ctx, j2_ctx.spamd.docker_image),
            cmd=str(run),
        )
        self.install_access(mode='500', owner=self.hdb.rsconf_db.run_u)
        self.install_resource('spamd/run.sh', j2_ctx, run)
