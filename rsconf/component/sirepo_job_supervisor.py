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
        self.__run_d = systemd.docker_unit_prepare(self, jc)
        self.__run_u = jc.rsconf_db.run_u

    def internal_build_write(self):
        from rsconf.component import db_bkp
        from rsconf.component import nginx
        from rsconf.component import docker

        jc = self.j2_ctx
        z = jc[self.name]
        systemd.docker_unit_enable(
            self,
            jc,
            image=z.docker_image,
            env=self.buildt.get_component('sirepo').sirepo_unit_env(self).pkupdate(
                PYENV_VERSION='py3',
            ),
            # cannot pass PYENV_VERSION=py3 to cmd
            cmd='pyenv exec sirepo job_supervisor',
            #TODO(robnagler) wanted by nginx
            volumes=[jc.sirepo.srdb.root]
        )
        docker.setup_cluster(
            self,
            jc.sirepo.job_driver.docker.hosts,
            jc.sirepo.job_driver.docker.tls_dir,
            run_u=self.__run_u,
            j2_ctx=self.j2_ctx,
        )
        nginx.install_vhost(
            self,
            vhost=z.vhost,
            backend_host=jc.sirepo.pkcli.job_supervisor.ip,
            backend_port=jc.sirepo.pkcli.job_supervisor.port,
            j2_ctx=jc,
        )

    def sirepo_config(self, sirepo):
        from rsconf.component import docker_registry

        jc = self.j2_ctx
        self.j2_ctx_pksetdefault(sirepo.j2_ctx)
        self.j2_ctx_pksetdefault(dict(
            sirepo_job_supervisor=dict(
                docker_image=lambda: docker_registry.absolute_image(jc, jc.sirepo.docker_image),
                vhost=lambda: 'job-supervisor-' + jc.sirepo.vhost,
            ),
        ))
        jc.sirepo.job.supervisor_uri = 'https://{}'.format(jc.sirepo_job_supervisor.vhost)
        for m in jc.sirepo.job_driver.modules:
            getattr(self, '_module_' + m)(jc)

    def _module_docker(self, jc):
        self.j2_ctx_pksetdefault({
            'sirepo.job_driver.docker': dict(
                parallel=dict(gigabytes=4, cores=4, slots_per_host=1),
                sequential=dict(gigabytes=1, slots_per_host=1),
                image=jc.sirepo_job_supervisor.docker_image,
                tls_dir=lambda: self.__run_d.join('docker_tls'),
            ),
        })

    def _module_local(self, jc):
        self.j2_ctx_pksetdefault({
            'sirepo.job_driver.local.slots': dict(parallel=1, sequential=1),
        })

    def _module_sbatch(self, jc):
        self.j2_ctx_pksetdefault({
            'sirepo.job_driver.sbatch.shifter_image': jc.sirepo.docker_image,
        })
