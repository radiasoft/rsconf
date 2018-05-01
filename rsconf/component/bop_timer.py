# -*- coding: utf-8 -*-
u"""create timers for bop apps

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import re
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio
import re

_ON_CALENDAR_RE = re.compile(r'^\*-\*-\S+\s+ (\d+):\d+:\d+$')

class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import bop

        # Must be after bop so bconf_f exists, and bop has to be on the machine
        self.buildt.require_component('bop')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.bop_timer
        for app_name in sorted(z.apps.keys()):
            app_vars = bop.merge_app_vars(j2_ctx, app_name)
            z.run_u = app_vars.run_u
            z.bconf_f = app_vars.bconf_f
            timers = z.apps[app_name].timers
            for t in sorted(timers.keys()):
                tv = timers[t]
                z.bash_script = tv.bash_script
                timer_name = '{}_{}'.format(app_name, t)
                run_d = systemd.timer_prepare(
                    self,
                    j2_ctx,
                    #TODO(robnagler) time zone
                    on_calendar=tv.on_calendar,
                    service_name=timer_name,
                )
                run_f = run_d.join('run')
                systemd.timer_enable(self, j2_ctx=j2_ctx, cmd=run_f, run_u=z.run_u)
                self.install_access(mode='500', owner=z.run_u)
                self.install_resource('bop_timer/run.sh', j2_ctx, run_f)
