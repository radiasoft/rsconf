# -*- coding: utf-8 -*-
"""create nginx configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pkio
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component

_DATA_DIR = "db"

_LOG_DIR = "log"

_MONGO_CONF_F = "mongod.conf"


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd

        self.buildt.require_component("base_all")
        self.j2_ctx, z = self.j2_ctx_init()
        # TODO(e-carlin): this is a goofy catch 22
        z.mongo_conf_path = self.j2_ctx.rsconf_db.host_run_d.join(self.name).join(
            _MONGO_CONF_F
        )
        z.run_d = systemd.custom_unit_prepare(self, self.j2_ctx, (z.mongo_conf_path,))

    def internal_build_write(self):
        from rsconf import systemd
        from rsconf.component import logrotate

        z = self.j2_ctx.mongod
        z.run_u = "mongod"
        z.run_d = self.j2_ctx.rsconf_db.host_run_d.join(self.name)
        z.data_d = z.run_d.join(_DATA_DIR)
        z.log_d = z.run_d.join(_LOG_DIR)
        z.pid_d = pkio.py_path("/run/mongod")
        z.pid_file_path = z.pid_d.join("mongod.pid")
        z.mongo_conf_path = z.run_d.join(_MONGO_CONF_F)
        self.install_access(mode="700", owner=z.run_u)
        for d in "run_d", "data_d", "log_d", "pid_d":
            self.install_directory(z[f"{d}"])
        self.install_access(mode="400", owner=z.run_u)
        self.install_resource(
            self.name + f"/{_MONGO_CONF_F}",
            self.j2_ctx,
            host_path=z.mongo_conf_path,
        )
        logrotate.install_conf(self, self.j2_ctx)
        systemd.install_unit_override(self, self.j2_ctx)
        self.append_root_bash_with_main(self.j2_ctx)
        systemd.custom_unit_enable(self, self.j2_ctx, run_u=z.run_u, run_group=z.run_u)
        self.rsconf_service_restart()
