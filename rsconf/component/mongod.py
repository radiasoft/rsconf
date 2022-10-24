# -*- coding: utf-8 -*-
"""create nginx configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pkio
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import systemd

_DATA_DIR = "db"

_LOG_DIR = "log"

_MONGO_CONF_F = "mongod.conf"


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd

        self.buildt.require_component("base_all")
        self.j2_ctx, z = self.j2_ctx_init()
        z.run_u = "mongod"
        d = systemd.custom_unit_prepare(self, self.j2_ctx)
        z.data_d = d.join(_DATA_DIR)
        z.log_d = d.join(_LOG_DIR)
        z.conf_f = d.join(_MONGO_CONF_F)

    def internal_build_write(self):
        from rsconf.component import logrotate

        z = self.j2_ctx.mongod
        self.append_root_bash_with_main(self.j2_ctx)
        logrotate.install_conf(self, self.j2_ctx)
        systemd.install_unit_override(self, self.j2_ctx)
        systemd.custom_unit_enable(self, self.j2_ctx, run_u=z.run_u, run_group=z.run_u)
        self.install_access(mode="700", owner=z.run_u)
        for d in "data_d", "log_d":
            self.install_directory(z[f"{d}"])
        self.install_access(mode="400", owner=z.run_u)
        self.install_resource(
            f"{self.name}/{_MONGO_CONF_F}",
            self.j2_ctx,
            host_path=z.conf_f,
        )
        self.rsconf_service_restart()
