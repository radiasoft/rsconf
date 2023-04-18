# -*- coding: utf-8 -*-
"""Timer to run sirepo test_http

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component


_SECRET = "SIREPO_UTIL_CREATE_TOKEN_SECRET"


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker_registry
        import pykern.pkdebug

        def _env_ok(k):
            if k.startswith("PYKERN_") or k.startswith("SIREPO_FEATURE_CONFIG_"):
                return not pykern.pkdebug.SECRETS_RE.search(k)
            return k == _SECRET or k.startswith("SIREPO_PKCLI_TEST_HTTP_SERVER")

        jc, z = self.j2_ctx_init()
        e = PKDict()
        for k, v in self.buildt.get_component("sirepo").sirepo_unit_env(self).items():
            if _env_ok(k):
                e[k] = v
        assert e.get(_SECRET), f"{_SECRET} not found in sirepo config"
        systemd.timer_prepare(
            self,
            jc,
            on_calendar=z.on_calendar,
            service_exec="sirepo test_http",
            is_docker=True,
        )
        e.pksetdefault(
            SIREPO_PKCLI_TEST_HTTP_SERVER_URI=f"https://{jc.sirepo.vhost}",
        )
        systemd.docker_unit_enable(
            self,
            env=e,
            image=docker_registry.absolute_image(
                self,
                j2_ctx=jc,
                image=jc.sirepo.docker_image,
                image_is_local=jc.sirepo.get("docker_image_is_local"),
            ),
            j2_ctx=jc,
            run_u=jc.rsconf_db.run_u,
        )
