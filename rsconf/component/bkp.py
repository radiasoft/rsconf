# -*- coding: utf-8 -*-
u"""create backup server config

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from rsconf import component
from rsconf import db
from rsconf import systemd


def append_authorized_key(compt, j2_ctx):
    compt.append_root_bash(
        "rsconf_edit_no_change_res=0 rsconf_append_authorized_key '{}' '{}'".format(
            j2_ctx.rsconf_db.root_u,
            j2_ctx.bkp.ssh_key,
        ),
    )


class T(component.T):
    def internal_build(self):
        self.buildt.require_component('base_all')

        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.bkp
        run_d = systemd.timer_prepare(self, j2_ctx)
        gv = 'bkp_exclude=(\n'
        for d in z.exclude:
            gv += "'--exclude={}'\n".format(d)
        gv += ')\n'
        for i in 'max_try', 'mirror_d':
            gv += "bkp_{}='{}'\n".format(i, z[i])
        gv += 'bkp_include=(\n'
        for d in z.include:
            gv += "    '{}'\n".format(d)
        gv += ')\n'
        z.global_vars = gv
        x = ''
        for h in z.hosts:
            x += "    primary_host '{}'\n".format(h)
        for h in z.secondaries:
            x += "    primary_secondary '{}'\n".format(h)
        z.main_cmds = x
        te = run_d.join('primary')
        systemd.timer_enable(
            self,
            j2_ctx=j2_ctx,
            on_calendar=z.on_calendar,
            timer_exec=te,
        )
        self.install_access(mode='500', owner=j2_ctx.rsconf_db.root_u)
        assert j2_ctx.rsconf_db.host == z.primary, \
            '{}: host must be in primary or secondaries'.format(
                j2_ctx.rsconf_db.host,
            )
        self.install_resource('bkp/primary.sh', j2_ctx, te)
