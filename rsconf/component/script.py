# -*- coding: utf-8 -*-
"""run arbitrary scripts and timers

:copyright: Copyright (c) 2023 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp, pkdlog
from rsconf import component


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd

        jc, z = self.j2_ctx_init()
        self.buildt.require_component(*(z.get("require_components", ["base_users"])))
        jc.pksetdefault(timers=PKDict)
        for k, v in z.timers.items():
            v._run_d = systemd.unit_run_d(jc, k)
            v._run_f = v._run_d.join("run")
            v.pksetdefault(run_u=jc.rsconf_db.root_u)
            for x in "on_calendar", "bash_script":
                if x not in v:
                    raise AssertionError(f"missing param={x} in script.timers.{k}")

    def internal_build_write(self):
        from rsconf import systemd

        jc = self.j2_ctx
        z = jc[self.name]
        if s := (z.get("rsconf_bash") or z.get("bash")):
            if z.get("bash"):
                pkdlog("script.bash is deprecated use script.rsconf_bash")
            self.append_root_bash(s)
        for k in sorted(z.timers.keys()):
            v = z.timers[k]
            z.curr_timer = v
            systemd.timer_prepare(
                self,
                jc,
                # TODO(robnagler) time zone
                on_calendar=v.on_calendar,
                service_name=k,
                timer_exec=v._run_f,
            )
            self.install_access(mode="500", owner=v.run_u)
            self.install_resource("script/timer.sh", host_path=v._run_f)
            systemd.timer_enable(self, run_u=v.run_u)
