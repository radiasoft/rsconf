"""create postgrey configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from rsconf import component


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd
        from rsconf.component import network

        self.buildt.require_component("base_all")
        jc, z = self.j2_ctx_init()
        z.run_d = systemd.unit_run_d(jc, self.name)
        z.update(
            db_d=z.run_d.join("db"),
            etc_d=z.run_d.join("etc"),
            run_u=self.hdb.rsconf_db.run_u,
            whitelist_clients="\n".join(
                self.buildt.get_component("network").trusted_nets()
            ),
        )

    def internal_build_write(self):
        from rsconf.component import bop
        from rsconf import systemd

        jc = self.j2_ctx
        z = jc[self.name]
        systemd.custom_unit_prepare(
            self,
            jc,
            watch_files=bop.install_perl_rpms(self, jc),
        )
        systemd.custom_unit_enable(self, jc)
        self.install_access(mode="700", owner=z.run_u)
        self.install_directory(z.run_d)
        self.install_directory(z.db_d)
        self.install_directory(z.etc_d)
        self.install_access(mode="400")
        self.install_resource2("postgrey_whitelist_recipients", z.etc_d)
        self.install_resource2("postgrey_whitelist_clients.local", z.etc_d)
