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
        jc, z = self.j2_ctx_init()
        run_d = systemd.docker_unit_prepare(self, jc)
        for m in jc.sirepo.job_driver.modules:
            getattr(self, '_module_' + m)(self, jc)
        z.pksetdefault(vhost=lambda: 'job-supervisor-' + jc.sirepo.vhost)
        self.j2_ctx_pksetdefault(
            'sirepo.job.supervisor_uri': 'https://{}'.format(z.vhost),
        )
    })

    def update_j2_ctx(self, sirepo):
        pass

    def _module_docker(self, jc):
        self.j2_ctx_pksetdefault(
            'sirepo.job_driver.docker': dict(
                parallel=dict(gigabytes=4, cores=4, slots_per_host=1),
                sequential=dict(gigabytes=1, slots_per_host=1),
                image=jc.sirepo.docker_image,
                tls_dir=lambda: self.__run_d.join('docker_tls'),
            ),
        )

    def _module_local(self, jc):
        self.j2_ctx_pksetdefault(
            'sirepo.job_driver.local.slots': dict(parallel=1, sequential=1),
        )

    def _module_sbatch(self, jc):
        self.j2_ctx_pksetdefault(
            shifter_image=jc.sirepo.docker_image,
        )

    def internal_build_write(self):

            docker.setup_cluster(
                self,
                docker_hosts,
                docker_tls_d,
                run_u=z.run_u,
                j2_ctx=j2_ctx,
            )
