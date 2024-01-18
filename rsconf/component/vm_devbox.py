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
        if self._is_main_instance():
            _create_user_instances()
            return
        self.buildt.require_component("network")
        z.run_d = systemd.unit_run_d(jc, self.name)
        z.run_u = jc.rsconf_db.run_u
        z.ssh_port = jc.vm_devbox_users.spec[self._user].ssh_port
        z.ssh_guest_host_key_f = "/etc/ssh/host_key"
        z.ssh_guest_identity_pub_f = "/etc/ssh/identity.pub"
        z.start_f = z.run_d.join("start")
        z.vm_hostname = f"{self._user}.{jc[self.module_name].vm_parent_domain}"
        systemd.unit_prepare(self, self.j2_ctx, watch_files=(z.start_f,))
        self._network(jc, z)
        self._ssh(jc, z)

    def internal_build_write(self):
        if self._is_main_instance():
            self.append_root_bash_with_main()
            return
        jc = self.j2_ctx
        z = jc[self.name]
        self.install_access(mode="500", owner=z.run_u)
        self.install_resource("vm_devbox/start.sh", host_path=z.start_f)
        self.install_access(mode="444", owner=jc.rsconf_db.root_u)
        self.install_resource(
            "vm_devbox/vm_devbox_unit_service", jc, jc.systemd.service_f
        )

    def _network(self, jc, z):
        self.buildt.get_component("network").add_public_tcp_ports([str(z.ssh_port)])

    def _ssh(self, jc, z):
        z.sshd_config_f = z.run_d.join("sshd_config")
        s = self.gen_identity_and_host_ssh_keys(jc, "host", encrypt_identity=True)
        z.pkupdate(
            PKDict(
                ssh_identity_pub_key=pkio.read_text(s.identity_pub_f),
                ssh_host_key=pkio.read_text(s.host_key_f),
            )
        )
