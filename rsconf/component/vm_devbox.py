"""Development in a vm

:copyright: Copyright (c) 2023 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pkconfig
from pykern import pkio
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import systemd

_VM_DIR = "v"


class T(component.T):
    def internal_build_compile(self):
        def _create_user_instances():
            for u in self.hdb.vm_devbox.users:
                self.buildt.build_component(
                    T(
                        f"{self.module_name}_{u}",
                        self.buildt,
                        _user=u,
                        module_name=self.module_name,
                    )
                )

        jc, z = self.j2_ctx_init()
        if self.name == "vm_devbox":
            _create_user_instances()
            return
        self.buildt.require_component("network")
        z.vm_d = systemd.custom_unit_prepare(self, self.j2_ctx).join(_VM_DIR)
        z.ssh_port = jc.base_users.spec[self._user].vm_devbox_ssh_port
        z.ssh_guest_host_key_f = "/etc/ssh/host_key"
        z.ssh_guest_identity_pub_f = "/etc/ssh/identity.pub"
        self._network(jc, z)
        self._ssh(jc, z)

    def internal_build_write(self):
        jc = self.j2_ctx
        if self.name == "vm_devbox":
            self.append_root_bash_with_main(jc)
            return
        z = jc[self.module_name]
        systemd.install_unit_override(self, self.j2_ctx)
        systemd.custom_unit_enable(
            self, self.j2_ctx, run_u=jc.rsconf_db.run_u, run_group=jc.rsconf_db.run_u
        )
        self.install_access(mode="700", owner=jc.rsconf_db.run_u)
        self.install_directory(z.vm_d)

    def _network(self, jc, z):
        n = self.buildt.get_component("network")
        n.add_public_tcp_ports([str(z.ssh_port)])

    def _ssh(self, jc, z):
        z.sshd_config_f = z.vm_d.join("sshd_config")
        s = super().gen_identity_and_host_ssh_keys(jc, "host", encrypt_identity=True)
        z.pkupdate(
            PKDict(
                ssh_identity_pub_key=pkio.read_text(s["identity_pub_f"]),
                ssh_host_key=pkio.read_text(s["host_key_f"]),
            )
        )
