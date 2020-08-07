# -*- coding: utf-8 -*-
u"""Timer to run sirepo test_http

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern.pkdebug import pkdp
from rsconf import component


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.sirepo_test_http
        systemd.timer_prepare(self, j2_ctx, on_calendar=z.on_calendar)
        systemd.docker_unit_enable(
            self,
            image=docker_registry.absolute_image(j2_ctx, j2_ctx.sirepo.docker_image),
            j2_ctx=j2_ctx,
            env=pkcollections.PKDict(
                SIREPO_PKCLI_TEST_HTTP_SERVER_URI=f'https://{j2_ctx.sirepo.vhost}',
            ),
            run_u=j2_ctx.rsconf_db.run_u,
            cmd='sirepo test_http',
        )
