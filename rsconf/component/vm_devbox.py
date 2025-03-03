"""Development in a vm

:copyright: Copyright (c) 2023 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern import pkconfig
from pykern import pkio
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
import re
import rsconf.component
import rsconf.db
import rsconf.systemd

_DEFAULT_VAGRANT_CPUS = 4
_DEFAULT_VAGRANT_MEMORY = 8192
# Allowable pattern enforced by vagrant
_VM_HOSTNAME_RE = "[a-z0-9][a-z0-9.-]*"
_LIB_VIRT_SUB_D = "libvirt"
_VAR_LIBVIRT_D = pkio.py_path("/var/lib/libvirt")


class T(rsconf.component.T):
    def internal_build_compile(self):
        def _create_user_instances():
            for u in self.hdb.vm_devbox.users:
                if not re.match(_VM_HOSTNAME_RE, u):
                    raise AssertionError(f"usernmae={u} must match /{_VM_HOSTNAME_RE}/")
                self.buildt.build_component(
                    T(
                        f"{self.module_name}_{u}",
                        self.buildt,
                        _user=u,
                        module_name=self.module_name,
                    )
                )

        jc, z = self.j2_ctx_init()
        z.root_u = jc.rsconf_db.root_u
        z.libvirt_d = self.j2_ctx.rsconf_db.host_run_d.join(_LIB_VIRT_SUB_D)
        if self._is_main_instance():
            _create_user_instances()
            return
        n = self.buildt.get_component("network")
        z.vm_hostname = n.assert_host(
            f"{self._user}.{jc[self.module_name].vm_parent_domain}",
        )
        z.run_d = rsconf.systemd.unit_run_d(jc, self.name)
        z.run_u = jc.rsconf_db.run_u
        z.local_ip = rsconf.db.LOCAL_IP
        z.ssh_port = jc.vm_devbox_users.spec[self._user].ssh_port
        z.ssh_guest_host_key_f = "/etc/ssh/host_key"
        z.ssh_guest_identity_pub_f = "/etc/ssh/identity.pub"
        z.start_f = z.run_d.join("start")
        z.stop_f = z.run_d.join("stop")
        z.timeout_start_min = jc[self.module_name].get("timeout_start_min", 15)
        z.vagrant_cpus = jc[self.module_name].get("vagrant_cpus", _DEFAULT_VAGRANT_CPUS)
        z.vagrant_memory = jc[self.module_name].get(
            "vagrant_memory", _DEFAULT_VAGRANT_MEMORY
        )
        rsconf.systemd.unit_prepare(
            self, self.j2_ctx, watch_files=(z.start_f, z.stop_f)
        )
        self._ssh(jc, z)

    def internal_build_write(self):
        jc = self.j2_ctx
        z = jc[self.name]
        if self._is_main_instance():
            self.install_access(mode="755", owner=z.root_u)
            self.install_directory(z.libvirt_d)
            self.install_symlink(z.libvirt_d, _VAR_LIBVIRT_D)
            self.append_root_bash_with_main()
            return
        self.install_access(mode="700", owner=z.run_u)
        self.install_directory(z.run_d)
        self.install_access(mode="500", owner=z.run_u)
        self.install_resource("vm_devbox/start.sh", host_path=z.start_f)
        self.install_resource("vm_devbox/stop.sh", host_path=z.stop_f)
        self.install_access(mode="444", owner=jc.rsconf_db.root_u)
        self.install_resource(
            "vm_devbox/vm_devbox_unit_service", jc, jc.systemd.service_f
        )

    def _ssh(self, jc, z):
        z.sshd_config_f = z.run_d.join("sshd_config")
        s = self.gen_identity_and_host_ssh_keys(jc, "host", encrypt_identity=True)
        z.pkupdate(
            PKDict(
                ssh_identity_pub_key=pkio.read_text(s.identity_pub_f),
                ssh_host_key=pkio.read_text(s.host_key_f),
            )
        )
