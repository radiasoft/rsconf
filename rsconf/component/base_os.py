"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import pykern.pkio
import rsconf.component

_JOURNAL_CONF_D = pykern.pkio.py_path("/etc/systemd/journald.conf.d")
_JOURNAL_SYSTEMD_D = pykern.pkio.py_path(
    "/etc/systemd/system/systemd-journald.service.d"
)
_SSHD_CONF_D = pykern.pkio.py_path("/etc/ssh")


class T(rsconf.component.T):
    def internal_build_compile(self):
        def _logical_volumes(vg):
            for k, v in vg.logical_volumes.items():
                if v.gigabytes == 0:
                    continue
                v = PKDict(v)
                v.name = k
                yield v

        def _volume_group_cmds(volume_groups):
            for n in sorted(volume_groups):
                for v in sorted(
                    _logical_volumes(volume_groups[n]), key=lambda x: x.mount_d
                ):
                    yield f"base_os_logical_volume '{v.name}' '{v.gigabytes}' '{n}' '{v.mount_d}' '{v.get('mode', 700)}'"

        jc, z = self.j2_ctx_init()
        self.j2_ctx_pksetdefault(
            PKDict(
                base_os=PKDict(
                    ip_forward=False,
                    volume_groups=PKDict(),
                ),
            ),
        )
        z.logical_volume_cmds = (
            "\n".join(_volume_group_cmds(z.volume_groups)) + "\n"
            if z.volume_groups
            else ""
        )
        self.service_prepare([_JOURNAL_CONF_D], name="systemd-journald")
        self.service_prepare([_SSHD_CONF_D], name="sshd")

    def internal_build_write(self):
        jc = self.j2_ctx
        z = jc.base_os
        # POSIT: postfix depends on base_os so build_write will not
        # execute postfix before base_os (this) build_write.
        z.has_component_postfix = self.buildt.has_component("postfix")
        self._install_local_dirs(jc.rsconf_db.local_dirs)
        self._install_local_files(jc.rsconf_db.local_files)
        self.install_resource2(
            "journald.conf",
            _JOURNAL_CONF_D,
            host_f="99-rsconf.conf",
            access="400",
            host_d_access=PKDict(mode="700", owner=jc.rsconf_db.root_u),
        )
        self.install_resource2("60-rsconf-base.conf", "/etc/sysctl.d")
        if "pam_limits" in z:
            # POSIT: /etc/security/limits.d/20-nproc.conf is the only file on CentOS 7
            self.reboot_on_change(
                [
                    self.install_resource2(
                        "pam_limits",
                        "/etc/security/limits.d",
                        host_f="99-rsconf.conf",
                    ),
                ],
            )
        self.install_resource2("hostname", "/etc", access="444")
        self.install_resource2("motd", "/etc")
        if self.hdb.rsconf_db.is_almalinux9:
            self.install_resource2(
                "99-journald-rsconf.conf",
                _JOURNAL_SYSTEMD_D,
                access="444",
                host_d_access="755",
            )
        self._pam_duo_and_sshd()
        self.append_root_bash_with_main(jc)

    def _install_local_dirs(self, values):
        x = self._local_file_defaults()
        for t in sorted(values):
            v = values[t].copy()
            v.pksetdefault(**x)
            self.install_access(mode=f"{v.mode:o}", owner=v.owner, group=v.group)
            self.install_directory(t)

    def _install_local_files(self, values):
        # TODO(robnagler) do we have to create directories and/or trigger on
        #  directory creation? For example, nginx rpm installs conf.d, which
        #  we will want to have local files for.
        x = self._local_file_defaults()
        for t in sorted(values):
            v = values[t].copy()
            if v._source.basename.endswith(".sh.jinja"):
                self.append_root_bash_with_file(v._source, self.j2_ctx)
                continue
            v.pksetdefault(**x)
            self.install_access(mode=f"{v.mode:o}", owner=v.owner, group=v.group)
            # Local files overwrite existing (distro) files but if a component tries
            # to overwrite a local file, and error will occur.
            self.install_abspath(v._source, t, ignore_exists=True)

    def _local_file_defaults(self):
        r = self.j2_ctx.rsconf_db.root_u
        return PKDict(mode=0o400, owner=r, group=r)

    def _pam_duo_and_sshd(self):
        def _jump(z):
            x = z.get("sshd_jump_users")
            return ",".join(x) if x else ""

        jc = self.j2_ctx
        z = jc.base_os
        z.want_sshd_pam_duo = "pam_duo" in z
        if z.want_sshd_pam_duo:
            self.install_resource2("duosecurity.repo", "/etc/yum.repos.d", access="444")
            self.install_rpm_key("gpg-pubkey-ff696172-62979e51")
            self.append_root_bash("rsconf_yum_install duo_unix")
            # These are read dynamically by sshd so don't need to be watched files
            self.install_resource2("pam_duo.conf", "/etc/duo", access="400")
        z.sshd_jump_users_match = _jump(z)
        # Must be after pam_duo in case duo is installed so that sshd is not broken
        self.install_resource2("sshd", "/etc/pam.d")
        self.install_resource2("sshd_config", _SSHD_CONF_D, access="400")
