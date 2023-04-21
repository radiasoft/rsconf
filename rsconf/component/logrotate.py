"""create logrotate config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkio
from rsconf import component
from rsconf import systemd

CONF_D = pkio.py_path("/etc/logrotate.d/")
CONF_F = pkio.py_path("/etc/logrotate.conf")


def install_conf(compt, j2_ctx, resource_d=None):
    compt.install_access(mode="400", owner=j2_ctx.rsconf_db.root_u)
    compt.install_resource(
        (resource_d or compt.name) + "/logrotate.conf",
        j2_ctx,
        CONF_D.join(compt.name),
    )


class T(component.T):
    def internal_build(self):
        self.buildt.require_component("base_users")
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.logrotate
        z.run_u = j2_ctx.rsconf_db.root_u
        z.conf_f = CONF_F
        z.verbose_flag = "--verbose" if z.get("verbose", False) else ""
        z.run_d = systemd.unit_run_d(j2_ctx, self.name)
        run = z.run_d.join("run")
        systemd.timer_prepare(self, j2_ctx, timer_exec=run, on_calendar=z.on_calendar)
        systemd.timer_enable(
            self,
            j2_ctx=j2_ctx,
            run_u=z.run_u,
        )
        self.install_access(mode="500", owner=z.run_u)
        self.install_resource("logrotate/run.sh", j2_ctx, run)
        self.install_access(mode="400")
        self.install_resource("logrotate/logrotate.conf", j2_ctx, z.conf_f)
        self.append_root_bash_with_main(j2_ctx)
