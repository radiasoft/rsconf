# -*- coding: utf-8 -*-
u"""setup proxy for jupyterhub backends

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from rsconf import component

class T(component.T):
    def internal_build(self):
        from rsconf.component import nginx

        self.buildt.require_component('nginx')
        j2_ctx = self.hdb.j2_ctx_copy()

        j2_ctx.setdefault(self.name, pkcollections.Dict())
        for h, vh in j2_ctx.jupyterhub.vhosts.items():
            nginx.install_vhost(
                self,
                vhost=vh,
                backend_host=h,
                backend_port=j2_ctx.jupyterhub.port,
                j2_ctx=j2_ctx,
            )
