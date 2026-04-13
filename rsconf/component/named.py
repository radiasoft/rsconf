"""Create named configuration

:copyright: Copyright (c) 2018-2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from rsconf import component


class T(component.T):
    def internal_build(self):
        from rsconf import db
        from rsconf import systemd

        def _listen_on(jc, z, nc):
            rv = db.LOCAL_IP + ";"
            if ip := nc.unchecked_public_ip():
                return f"{rv} {ip};"
            if jc.rsconf_db.channel != "dev":
                raise AssertionError("must have a public ip to run named")
            return rv

        self.buildt.require_component("base_all")
        # need bind installed
        self.append_root_bash("rsconf_yum_install bind")
        jc, z = self.j2_ctx_init()
        z.run_d = systemd.custom_unit_prepare(self, jc)
        nc = self.buildt.get_component("network")
        nc.add_public_tcp_ports(["domain"])
        nc.add_public_udp_ports(["domain"])
        self.j2_ctx_pksetdefault(
            PKDict(
                named=PKDict(
                    # POSIT: same paths used in the build server
                    db_path_d=lambda: db.db_path(jc, "named", directory=True),
                    # Default is 10K+
                    max_sockets=1024,
                    # Default is number of cores, which is ridiculous
                    num_threads=4,
                    run_group="named",
                    run_u=jc.rsconf_db.root_u,
                    listen_on=lambda: _listen_on(jc, z, nc),
                ),
            ),
        )
        z.db_d = z.run_d.join("db")
        z.conf_f = z.db_d.join("named.conf")
        z.zones_f = z.db_d.join("zones.conf")

    def internal_build_write(self):
        from rsconf import systemd
        from pykern import pkio

        jc = self.j2_ctx
        z = jc[self.name]
        self.install_access(mode="750", owner=z.run_u, group=z.run_u)
        self.install_directory(z.run_d)
        self.install_access(mode="750", owner=z.run_u, group=z.run_group)
        self.install_directory(z.db_d)
        self.install_access(mode="440")
        for f in pkio.sorted_glob(z.db_path_d.join("*")):
            self.install_abspath(f, z.db_d.join(f.basename))
        self.install_resource("named/named.conf", jc, z.conf_f)
        systemd.custom_unit_enable(
            self,
            jc,
            run_u=z.run_u,
            run_group=z.run_group,
            run_d_mode="770",
        )
