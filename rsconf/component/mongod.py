# -*- coding: utf-8 -*-
"""create nginx configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component

_DATA_DIR = "db"

_MONGO_CONF_F = "/etc/mongod.conf"


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("base_all")
        self.j2_ctx, _ = self.j2_ctx_init()

    def internal_build_write(self):
        from rsconf import systemd

        z = self.j2_ctx.mongod
        z.run_u = "mongod"
        d = self.j2_ctx.rsconf_db.host_run_d.join(self.name)
        z.data_d = d.join(_DATA_DIR)
        self.install_access(mode="700", owner=z.run_u)
        self.install_directory(d)
        self.install_directory(z.data_d)
        self.install_access(mode="400", owner=z.run_u)
        self.install_resource(
            self.name + "/mongod.conf",
            self.j2_ctx,
            host_path=_MONGO_CONF_F,
        )
        self.append_root_bash_with_main(self.j2_ctx)
        systemd.unit_enable(self, self.j2_ctx)
        self.service_prepare([_MONGO_CONF_F])
        self.rsconf_service_restart()
