# -*- coding: utf-8 -*-
u"""setup proxy for jupyterhub backends

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern.pkdebug import pkdp
from rsconf import component


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component('nginx')
        jc, z = self.j2_ctx_init()
        z.pksetdefault(listen_any=False)

    def internal_build_write(self):
        from rsconf.component import nginx

        jc = self.j2_ctx
        for h, vh in jc.jupyterhub.vhosts.items():
            nginx.install_vhost(
                self,
                vhost=vh,
                backend_host=h,
                backend_port=jc.jupyterhub.api_port,
                j2_ctx=jc,
                listen_any=jc.jupyterhub_proxy.listen_any,
            )
