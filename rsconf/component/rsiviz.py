# -*- coding: utf-8 -*-
"""rsiviz (nginx + IndeX)

:copyright: Copyright (c) 2019-2023 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pkconfig
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("nginx")
        jc, z = self.j2_ctx_init()
        if "index_uri_secret" not in z:
            z.index_uri_secret = db.random_string()
        z.global_resources.viz3d.index_uri_fmt = (
            f"https://{z.index_vhost}:{{}}/{z.index_uri_secret}/"
        )
        z.global_resources.viz3d.index_allowed_origins = f" ".join(
            [
                f"{z.index_vhost}:{p}"
                for p in range(
                    jc.sirepo.global_resources.public_ports_min,
                    jc.sirepo.global_resources.public_ports_max,
                )
            ]
        )

    def internal_build_write(self):
        from rsconf.component import nginx

        nginx.install_vhost(
            self,
            vhost=self.j2_ctx.rsiviz.index_vhost,
            j2_ctx=self.j2_ctx,
        )

    def sirepo_config(self, sirepo):
        sirepo.j2_ctx.rsiviz.global_resources.viz3d = (
            self.j2_ctx.rsiviz.global_resources.viz3d
        )
