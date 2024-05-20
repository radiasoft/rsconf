"""create backup server config

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from pykern import pkcollections
from rsconf import component
from rsconf import db
from rsconf import systemd


def append_authorized_key(compt, j2_ctx):
    compt.append_root_bash(
        "rsconf_append_authorized_key '{}' '{}'".format(
            j2_ctx.rsconf_db.root_u,
            j2_ctx.bkp.ssh_key,
        ),
    )


class T(component.T):
    def internal_build(self):
        self.buildt.require_component("base_all")

        jc = self.hdb.j2_ctx_copy()
        z = jc.bkp
        z.run_u = jc.rsconf_db.root_u
        z.run_d = systemd.unit_run_d(jc, self.name)
        secondary_setup = None
        if jc.rsconf_db.host == z.primary:
            self._primary(jc, z)
            n = "primary"
        else:
            secondary_setup = self._secondary(jc, z)
            n = "secondary"
        te = z.run_d.join(n)
        systemd.timer_prepare(self, jc, timer_exec=te, on_calendar=z.on_calendar)
        self.install_access(mode="500", owner=z.run_u)
        self.install_resource("bkp/{}.sh".format(n), jc, te)
        if secondary_setup:
            self.install_abspath(
                secondary_setup,
                z.run_d.join(secondary_setup.purebasename),
            )
        systemd.timer_enable(self, j2_ctx=jc, run_u=z.run_u)

    def _primary(self, jc, z):
        gv = "bkp_exclude=(\n"
        for d in z.exclude:
            gv += "'--exclude={}'\n".format(d)
        gv += ")\n"
        gv += "declare -A bkp_exclude_for_host=(\n"
        for h, v in z.get("exclude_for_host", {}).items():
            gv += f"['{h}']='"
            for d in v:
                assert " " not in d, f'dir="{d}" contains a space exclude_for_host={h}'
                gv += f" --exclude={d}"
            gv += "'\n"
        gv += ")\n"
        for i in "archive_d", "max_try", "mirror_d":
            gv += "bkp_{}='{}'\n".format(i, z[i])
        gv += "bkp_include=(\n"
        for d in z.include:
            gv += "    '{}'\n".format(d)
        gv += ")\n"
        gv += "bkp_log_dirs=(\n"
        for d in z.log_dirs:
            # POSIT: bkp_log_dirs looks in the mirror_d so relative needed
            gv += "    '{}'\n".format(str(d).lstrip("/"))
        gv += ")\n"
        z.global_vars = gv
        z.host_cmds = "".join(
            ["    primary_host '{}'\n".format(h) for h in z.hosts],
        )
        z.secondary_cmds = "".join(
            ["    primary_secondary '{}'\n".format(h) for h in z.secondaries],
        )
        z.simple_mirror_cmds = ""
        for tgt in sorted(z.simple_mirrors.keys()):
            for src in z.simple_mirrors[tgt]:
                z.simple_mirror_cmds += "    primary_simple_mirror '{}' '{}'\n".format(
                    src,
                    tgt,
                )

    def _secondary(self, jc, z):
        z.setdefault("secondary_copy_unmount_cmds", "")
        return z.setdefault("secondary_setup_f", None)
