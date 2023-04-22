# -*- coding: utf-8 -*-
"""create postgrey configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pkcollections
from pykern.pkdebug import pkdp
from rsconf import component


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import network
        from rsconf.component import bop

        self.buildt.require_component("base_all")
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.setdefault("postgrey", pkcollections.Dict())
        nc = self.buildt.get_component("network")
        z.whitelist_clients = "\n".join(nc.trusted_nets())
        watch = bop.install_perl_rpms(self, j2_ctx)
        run_d = systemd.custom_unit_prepare(self, j2_ctx, watch_files=watch)
        z.update(
            dbdir=run_d.join("db"),
            etc=run_d.join("etc"),
        )
        systemd.custom_unit_enable(self, j2_ctx)
        self.install_access(mode="700", owner=self.hdb.rsconf_db.run_u)
        self.install_directory(run_d)
        self.install_directory(j2_ctx.postgrey.dbdir)
        self.install_directory(j2_ctx.postgrey.etc)
        self.install_access(mode="400")
        self.install_resource(
            "postgrey/postgrey_whitelist_recipients",
            j2_ctx,
            j2_ctx.postgrey.etc.join("postgrey_whitelist_recipients"),
        )
        self.install_resource(
            "postgrey/postgrey_whitelist_clients.local",
            j2_ctx,
            j2_ctx.postgrey.etc.join("postgrey_whitelist_clients.local"),
        )
