# -*- coding: utf-8 -*-
u"""sirepo.job_supervisor

:copyright: Copyright (c) 2019 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from rsconf import systemd
import base64
import os

class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component('docker', 'nginx')
        jc = j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.sirepo_job_supervisor
        run_d = systemd.docker_unit_prepare(self, j2_ctx)

            docker_tls_d = z.run_d.join('docker_tls')
                params,
                j2_ctx,
                (
                    'sirepo.job_driver.docker.parallel_gigabytes',
                    'sirepo.job_driver.docker.sequential_gigabytes',
                    'sirepo.mpi_cores',
                ),
            )
    def sirepo_server_setup(self, j2_ctx):

        'sirepo.server.db_dir': z.db_d,

        z.docker_image
        z.db_d = run_d.join(_DB_SUBDIR)


    def internal_build_write(self):

            docker.setup_cluster(
                self,
                docker_hosts,
                docker_tls_d,
                run_u=z.run_u,
                j2_ctx=j2_ctx,
            )
