"""create bivio_named configuration

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from rsconf import component


class T(component.T):
    def internal_build(self):
        from rsconf import db
        from rsconf import systemd
        from rsconf.component import bop

        self.buildt.require_component("base_all")
        # need bind installed
        self.append_root_bash("rsconf_yum_install bind")
        self.j2_ctx = self.hdb.j2_ctx_copy()
        jc = self.j2_ctx
        run_d = systemd.custom_unit_prepare(self, jc)
        jc.setdefault("named", PKDict()).update(
            dbdir=run_d.join("db"),
            etc=run_d.join("etc"),
        )
        z = jc.named
        z.listen_on = f"{db.LOCAL_IP};"
        nc = self.buildt.get_component("network")
        nc.add_public_tcp_ports(["domain"])
        nc.add_public_udp_ports(["domain"])
        ip = nc.unchecked_public_ip()
        if ip:
            z.listen_on += " " + ip + ";"
        elif jc.rsconf_db.channel != "dev":
            raise AssertionError("must have a public ip to run named")
        z.run_group = "named"
        # Default is 10K+
        z.setdefault("max_sockets", 1024)
        # Default is number of cores, which is ridiculous
        z.setdefault("num_threads", 4)
        z.run_u = jc.rsconf_db.root_u
        # POSIT: same directory as in update.sh
        z.db_d = run_d.join("db")
        z.conf_f = z.db_d.join("named.conf")

    def internal_build_write(self):
        from rsconf import systemd
        import pykern.pkio

        jc = self.j2_ctx
        z = jc.named
        # runtime_d (/run) set by custom_unit_prepare
        self.install_access(mode="750", owner=z.run_u, group=z.run_group)
        self.install_directory(z.db_d)
        self.install_access(mode="440", owner=z.run_u, group=z.run_group)
        for f in pykern.pkio.sorted_glob(self.db_path("named", directory=True).join("*")):
            self.install_abspath(f, z.db_d.join(f.basename))
        self.install_access(mode="444", owner="root", group="root")
        self.install_joined_lines(
            [f'OPTIONS="-c {z.conf_f}"'],
            "/etc/sysconfig/named",
        )
        self.install_resource("named/named.conf", jc, z.conf_f)
        systemd.custom_unit_enable(
            self,
            jc,
            run_u=z.run_u,
            run_group=z.run_group,
            run_d_mode="770",
        )
