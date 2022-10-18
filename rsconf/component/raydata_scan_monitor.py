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

_DB_SUBDIR = "db"


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("docker")
        jc, z = self.j2_ctx_init()
        z.db_d = systemd.docker_unit_prepare(self, jc).join(_DB_SUBDIR)
        z.intake_d = jc.systemd.run_d.join("intake")

    def internal_build_write(self):

        jc = self.j2_ctx
        z = jc[self.name]
        systemd.docker_unit_enable(
            self,
            jc,
            image=z.docker_image,
            env=self._unit_env(z),
            cmd="raydata scan_monitor",
            volumes=[
                z.db_d,
                [
                    z.intake_d,
                    # POSIT: python -c "import databroker; print(databroker.catalog_search_path())"
                    f"/home/{jc.rsconf_db.run_u}/.local/share/intake",
                    "rw",
                ],
            ],
        )
        self.install_access(mode="700", owner=jc.rsconf_db.run_u)
        self.install_directory(z.db_d)
        self.install_directory(z.intake_d)

    def _unit_env(self, z):
        return pkconfig.to_environ(
            ["raydata.pkcli.*"],
            values=z.pkmerge(
                PKDict(raydata=PKDict(pkcli=PKDict(scan_monitor=PKDict(db_dir=z.db_d))))
            ),
        )
