"""create spamassassin spamd configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from rsconf import component
from pykern import pkio


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd
        from rsconf.component import network

        self.buildt.require_component("base_all")
        jc, z = self.j2_ctx_init()
        z.conf_d = pkio.py_path("/etc/mail/spamassassin")
        z.sa_update_keys_d = z.conf_d.join("sa-update-keys")
        z.trusted_networks = " ".join(
            self.buildt.get_component("network").trusted_nets()
        )
        z.run_d = systemd.unit_run_d(jc, self.name)
        z.log_postrotate_f = z.run_d.join("log_postrotate")
        z.socket_d = pkio.py_path("/run/spamd")
        z.socket_path = pkio.py_path("/run/spamd/spamd.sock")

    def internal_build_write(self):
        from rsconf import systemd
        from rsconf.component import logrotate
        from rsconf.component import bop

        jc = self.j2_ctx
        z = jc[self.name]
        systemd.custom_unit_prepare(
            self, jc, watch_files=bop.install_perl_rpms(self, jc) + [z.conf_d]
        )
        self.install_access(mode="755", owner=jc.rsconf_db.run_u)
        self.install_directory(z.conf_d)
        self.install_directory(z.socket_d)
        # TODO: should be systemd since it knows the directory/perms
        self.install_access(mode="700")
        self.install_directory(z.run_d)
        self.install_access(mode="500")
        self.install_resource("spamd/log_postrotate.sh", jc, z.log_postrotate_f)
        self.install_access(mode="444")
        self.install_resource(
            "spamd/spamc.conf",
            jc,
            z.conf_d.join("spamc.conf"),
        )
        logrotate.install_conf(self, jc)
        self.append_root_bash_with_main(jc)
        systemd.custom_unit_enable(self, jc)
