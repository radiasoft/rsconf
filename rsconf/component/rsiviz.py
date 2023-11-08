# -*- coding: utf-8 -*-
"""rsiviz (nginx + IndeX)

:copyright: Copyright (c) 2019 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from rsconf import systemd


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("nginx")
        jc, z = self.j2_ctx_init()
        self.__host = self.hdb.rsconf_db.host
        if "index_uri_secret" not in z:
            z.index_uri_secret = db.random_string()
        z.global_resources.index_uri_fmt = (
            f"https://{self.__host}:{{}}/{z.index_uri_secret}/"
        )

    def internal_build_write(self):
        from rsconf.component import nginx

        nginx.install_vhost(
            self,
            vhost=self.__host,
            j2_ctx=self.j2_ctx,
        )

    def sirepo_config(self, sirepo):
        sirepo.j2_ctx.rsiviz.global_resources.index_uri_fmt = (
            self.j2_ctx.rsiviz.global_resources.index_uri_fmt
        )
