# -*- coding: utf-8 -*-
"""create database backup config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from rsconf import component
from rsconf import db
from rsconf import systemd


DEFAULTS = pkcollections.Dict(
    # Backups are big, and we copy them off to the bkp server
    # so this is really good enough in case bkp server is dead
    # for a day or two
    max_copies=4,
    script_name="db_bkp.sh",
    subdir_name="db_bkp",
)


def install_script_and_subdir(compt, j2_ctx, run_u, run_d, resource_d=None):
    # Don't need to make directly executable, is sourced
    z = set_defaults(j2_ctx)
    compt.install_access(mode="400", owner=run_u)
    compt.install_resource(
        (resource_d or compt.name) + "/" + z.script_name,
        j2_ctx,
        run_d.join(z.script_name),
    )
    compt.install_access(mode="700")
    compt.install_directory(run_d.join(z.subdir_name))


def set_defaults(j2_ctx):
    z = j2_ctx.db_bkp
    for k, v in DEFAULTS.items():
        z.setdefault(k, v)
    return z


class T(component.T):
    def internal_build(self):
        self.buildt.require_component("base_all")

        j2_ctx = self.hdb.j2_ctx_copy()
        z = set_defaults(j2_ctx)
        z.run_u = j2_ctx.rsconf_db.root_u
        run_d = systemd.timer_prepare(self, j2_ctx, on_calendar=z.on_calendar)
        run_f = run_d.join("run")
        systemd.timer_enable(
            self,
            j2_ctx=j2_ctx,
            cmd=run_f,
            run_u=z.run_u,
        )
        self.install_access(mode="500", owner=z.run_u)
        self.install_resource("db_bkp/run.sh", j2_ctx, run_f)
