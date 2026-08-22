"""install the common perl rpms

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from rsconf import component

COMMON_RPMS = ("bivio-perl", "perl-Bivio")


def install_rpms(compt, j2_ctx, rpms):
    """Installs `rpms`, returning the rpm files to watch"""
    c = _rpm_channel(j2_ctx)
    return [compt.install_perl_rpm(j2_ctx, r, channel=c) for r in rpms]


def watch_files(compt):
    """rpms installed by `T` for `systemd.custom_unit_prepare`"""
    return list(compt.buildt.get_component("perl_rpms", in_write_queue=False).rpm_files)


class T(component.T):
    def internal_build_compile(self):
        """Installs `COMMON_RPMS`

        Must be during build_compile, because `component.T.install_perl_rpm`
        is first-caller-wins, and components which write during build_compile
        would otherwise install the rpms in a script which runs after the
        components which require them.
        """
        self.buildt.require_component("base_all")
        self.append_root_bash("install_repo_eval biviosoftware/container-perl base")
        self.rpm_files = install_rpms(self, self.hdb.j2_ctx_copy(), COMMON_RPMS)


def _rpm_channel(j2_ctx):
    """Channel for all perl rpms; defaults to the host's channel"""
    return j2_ctx.get("perl_rpms", PKDict()).get(
        "rpm_channel", j2_ctx.rsconf_db.channel
    )
