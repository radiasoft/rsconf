# -*- coding: utf-8 -*-
u"""create database backup config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from rsconf import component
from rsconf import db
from rsconf import systemd


SUBDIR_NAME = 'db_bkp'
SCRIPT_NAME = 'db_bkp.sh'

def install_script_and_subdir(compt, j2_ctx, run_u, run_d, resource_d=None):
    # Don't need to make directly executable, is sourced
    compt.install_access(mode='400', owner=run_u)
    compt.install_resource(
        (resource_d or compt.name) + '/' + SCRIPT_NAME,
        j2_ctx,
        run_d.join(SCRIPT_NAME),
    )
    compt.install_access(mode='700')
    compt.install_directory(run_d.join(SUBDIR_NAME))


class T(component.T):
    def internal_build(self):
        self.buildt.require_component('base_all')

        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.db_bkp
        z.run_u = j2_ctx.rsconf_db.root_u
        run_d = systemd.timer_prepare(self, j2_ctx)
        run_f = run_d.join('run')
        z.script_name = SCRIPT_NAME
        z.subdir_name = SUBDIR_NAME
        systemd.timer_enable(
            self,
            j2_ctx=j2_ctx,
            on_calendar=z.on_calendar,
            timer_exec=run_f,
            run_u=z.run_u,
        )
        self.install_access(mode='500', owner=z.run_u)
        self.install_resource('db_bkp/run.sh', j2_ctx, run_f)
