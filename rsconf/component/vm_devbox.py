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
                    )
                )

        def _installer_cmd(z):
            v = PKDict(
                cmd="vagrant-sirepo-dev",
                vagrant_dev_cpus=z.vagrant_cpus,
                vagrant_dev_memory=z.vagrant_memory,
                vagrant_dev_vm_devbox=1,
            )
            if z.fedora_version:
                v.cmd = "vagrant-dev fedora"
                v.install_version_fedora = z.fedora_version
            # Not quoted properly for bash. None of the values needs
            # to be escaped, because they should not contain specials and
            # the source is trusted.
            c = [f"bash -s {v.pkdel('cmd')} {z.vm_hostname}"]
            return " ".join(_join_items(v) + c)

        def _join_items(pairs):
            return [f"{k}={pairs[k]}" for k in sorted(pairs.keys())]

        self.buildt.require_component("network")
        jc, z = self.j2_ctx_init()
        pkdp(z)
        z.root_u = jc.rsconf_db.root_u
        z.libvirt_d = self.j2_ctx.rsconf_db.host_run_d.join(_LIB_VIRT_SUB_D)
        if self._is_main_instance():
            _create_user_instances()
            return
        n = self.buildt.get_component("network")
        z.pksetdefault(
            **jc[self.module_name],
        )
        if "ssh_port" not in z:
            raise AssertionError(f"missing vm_devbox.ssh_port for user={self._user}")
        z.pksetdefault(
            fedora_version=None,
            timeout_start_min=15,
            vagrant_cpus=_DEFAULT_VAGRANT_CPUS,
            vagrant_memory=_DEFAULT_VAGRANT_MEMORY,
        )
        z.vm_hostname = n.assert_host(f"{self._user}.{z.vm_parent_domain}")
        z.run_d = rsconf.systemd.unit_run_d(jc, self.name)
        z.run_u = jc.rsconf_db.run_u
        z.local_ip = rsconf.db.LOCAL_IP
        z.ssh_guest_host_key_f = "/etc/ssh/host_key"
        z.ssh_guest_authorized_keys_f = rsconf.db.user_home_path(z.run_u).join(
            ".ssh/authorized_keys"
        )
        z.start_f = z.run_d.join("start")
        z.stop_f = z.run_d.join("stop")
        z.installer_cmd = _installer_cmd(z)
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
