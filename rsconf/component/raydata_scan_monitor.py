# -*- coding: utf-8 -*-
"""raydata.pkcli.scan_monitor

:copyright: Copyright (c) 2019 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pkconfig
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import systemd
import copy
import rsconf.db

_DB_SUBDIR = "db"

_INTAKE_D = "intake"


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("docker")
        jc, z = self.j2_ctx_init()
        z.run_u = jc.rsconf_db.run_u
        z._run_d = systemd.docker_unit_prepare(
            self,
            jc,
            docker_exec="sirepo raydata scan_monitor",
        )
        z.db_d = z._run_d.join(_DB_SUBDIR)
        z.intake_d = z._run_d.join(_INTAKE_D)
        jc.sirepo.raydata.scan_monitor.db_dir = z.db_d

    def internal_build_write(self):
        jc = self.j2_ctx
        z = jc[self.name]
        systemd.docker_unit_enable(
            self,
            jc,
            image=z.docker_image,
            env=self.python_service_env(
                values=PKDict(
                    pykern=jc.pykern, sirepo=PKDict(raydata=jc.sirepo.raydata)
                )
            ),
            volumes=[
                z.db_d,
                [
                    z.intake_d,
                    # POSIT: databroker.catalog_search_path()
                    f"{rsconf.db.user_home_path(z.run_u)}/.local/share/intake",
                    "rw",
                ],
            ],
        )
        self.install_access(mode="700", owner=z.run_u)
        self.install_directory(z.db_d)
        self.install_directory(z.intake_d)

    def sirepo_config(self, sirepo):
        self.j2_ctx_pksetdefault(sirepo.j2_ctx)
