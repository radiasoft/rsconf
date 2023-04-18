# -*- coding: utf-8 -*-
"""?

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from rsconf import component


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        self.buildt.require_component("docker")

        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.github_bkp
        z.run_u = j2_ctx.rsconf_db.run_u
        run_d = systemd.unit_run_d(j2_ctx, self.name)
        z.db_d = run_d.join("db")
        z.run_f = run_d.join("run")
        systemd.timer_prepare(
            self,
            j2_ctx,
            on_calendar=z.on_calendar,
            docker_exec=z.run_f,
            is_docker=True,
        )
        env = pkcollections.Dict(
            PYKERN_PKCLI_GITHUB_EXCLUDE_RE=z.exclude_re,
            PYKERN_PKCLI_GITHUB_PASSWORD=z.password,
            PYKERN_PKCLI_GITHUB_TEST_MODE=z.setdefault("test_mode", False),
            PYKERN_PKCLI_GITHUB_USER=z.user,
        )
        systemd.docker_unit_enable(
            self,
            image=docker_registry.absolute_image(self, j2_ctx),
            j2_ctx=j2_ctx,
            env=env,
            run_u=z.run_u,
        )
        self.install_access(mode="500", owner=z.run_u)
        self.install_resource("github_bkp/run.sh", j2_ctx, z.run_f)
        self.install_access(mode="700")
        self.install_directory(z.db_d)
