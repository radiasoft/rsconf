# -*- coding: utf-8 -*-
u"""mpi_cluster

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component

class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker
        from rsconf.component import docker_registry

        self.buildt.require_component('docker')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.mpi_cluster
        z.run_d = systemd.unit_run_d(j2_ctx, self.name)
        z.docker_tls_d = z.run_d.join('docker_tls')
        z.run_u = j2_ctx.rsconf_db.run_u
        z.docker_image = docker_registry.absolute_image(j2_ctx, z.docker_image)
        self.install_access(mode='700', owner=z.run_u)
        self.install_directory(z.run_d)
        self.install_access(mode='500')
        self.install_resource(
            'mpi_cluster/start.sh',
            j2_ctx,
            z.run_d.join('start'),
        )
        docker.setup_cluster(
            self,
            z.workers,
            z.docker_tls_d,
            run_u=z.run_u,
            j2_ctx=j2_ctx,
        )
