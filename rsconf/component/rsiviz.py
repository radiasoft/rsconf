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
import socket


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("nginx")
        jc, z = self.j2_ctx_init()

        n = self.buildt.get_component("network")
        if pkconfig.in_dev_mode():
            h = jc.rsconf_db.host
        else:
            i = n.unchecked_public_ip()
            assert i, "must have a public ip outside of dev"
            h = socket.gethostbyaddr(i)[0]
        self.__host = h
        if "index_uri_secret" not in z:
            z.index_uri_secret = db.random_string()
        z.global_resources.viz3d.index_uri_fmt = (
            f"https://{self.__host}:{{}}/{z.index_uri_secret}/"
        )
        z.global_resources.viz3d.index_allowed_origins = f" ".join(
            [
                f"{self.__host}:{p}"
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
            vhost=self.__host,
            j2_ctx=self.j2_ctx,
        )

    def sirepo_config(self, sirepo):
        sirepo.j2_ctx.rsiviz.global_resources.viz3d = (
            self.j2_ctx.rsiviz.global_resources.viz3d
        )
