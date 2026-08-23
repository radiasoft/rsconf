"""install the common perl rpms

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from rsconf import component

COMMON_RPMS = ("bivio-perl", "perl-Bivio")


def rpm_channel(compt):
    """Channel for all perl rpms; defaults to the host's channel"""
    return _self(compt).rpm_channel


def watch_files(compt):
    """rpm files for `COMMON_RPMS`, which `T` installs

    Returns:
        list: for `systemd.custom_unit_prepare`
    """
    return list(_self(compt).rpm_files)


class T(component.T):
    def internal_build_compile(self):
        """Installs `COMMON_RPMS`"""
        self.buildt.require_component("base_all")
        jc, z = self.j2_ctx_init()
        self.rpm_channel = z.setdefault("rpm_channel", jc.rsconf_db.channel)
        self.append_root_bash("install_repo_eval biviosoftware/container-perl base")
        self.rpm_files = [
            self.install_perl_rpm(jc, r, channel=self.rpm_channel) for r in COMMON_RPMS
        ]


def _self(compt):
    return compt.buildt.get_component("perl_rpms", in_write_queue=False)
