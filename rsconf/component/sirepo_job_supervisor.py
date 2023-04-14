# -*- coding: utf-8 -*-
"""sirepo.job_supervisor

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
        self.buildt.require_component("docker", "nginx")
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
            env=self.buildt.get_component("sirepo").sirepo_unit_env(self),
            cmd="sirepo job_supervisor",
            # TODO(robnagler) wanted by nginx
            volumes=[jc.sirepo.srdb.root],
        )
        docker.setup_cluster(
            self,
            jc.sirepo.job_driver.docker.hosts,
            jc.sirepo.job_driver.docker.tls_dir,
            run_u=self.__run_u,
            j2_ctx=self.j2_ctx,
        )
        for v in sorted(self._vhosts):
            nginx.install_vhost(
                self,
                vhost=v,
                backend_host=jc.sirepo.pkcli.job_supervisor.ip,
                backend_port=jc.sirepo.pkcli.job_supervisor.port,
                j2_ctx=jc,
            )

    def sirepo_config(self, sirepo):
        from rsconf.component import docker_registry

        jc = self.j2_ctx
        self._vhosts = set()
        self.j2_ctx_pksetdefault(sirepo.j2_ctx)
        self.j2_ctx_pksetdefault(
            dict(
                sirepo_job_supervisor=dict(
                    docker_image=lambda: docker_registry.absolute_image(sirepo),
                    docker_image_is_local=lambda: docker_registry.image_is_local(
                        sirepo
                    ),
                ),
            )
        )
        for m in jc.sirepo.job_driver.modules:
            getattr(self, "_module_" + m)(jc)
            self._uri(m)

    def _module_docker(self, jc):
        self.j2_ctx_pksetdefault(
            {
                "sirepo.job_driver.docker": dict(
                    parallel=dict(gigabytes=4, cores=4, slots_per_host=1),
                    sequential=dict(gigabytes=1, slots_per_host=1),
                    image=jc.sirepo_job_supervisor.docker_image,
                    tls_dir=lambda: self.__run_d.join("docker_tls"),
                ),
            }
        )

    def _module_local(self, jc):
        self.j2_ctx_pksetdefault(
            {
                "sirepo.job_driver.local.slots": dict(parallel=1, sequential=1),
            }
        )

    def _module_sbatch(self, jc):
        self.j2_ctx_pksetdefault(
            {
                "sirepo.job_driver.sbatch.shifter_image": "radiasoft/sirepo:"
                + jc.rsconf_db.channel,
            }
        )

    def _uri(self, module):
        p = "sirepo.job_driver.{}.".format(module)
        v = p + "vhost"
        self.j2_ctx_pksetdefault(
            {
                v: lambda: module + "-job-supervisor-" + self.j2_ctx.sirepo.vhost,
            }
        )
        v = self.j2_ctx.pknested_get(v)
        self._vhosts.add(v)
        self.j2_ctx.sirepo.job_driver[module].supervisor_uri = "https://{}".format(v)
