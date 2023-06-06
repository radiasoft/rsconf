# -*- coding: utf-8 -*-
"""rsaccounting server and proxy

:copyright: Copyright (c) 2023 RadiaSoft LLC.  All Rights Reserved.
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
        z._run_u = jc.rsconf_db.run_u
        systemd.custom_unit_prepare(self, jc)

    def internal_build_write(self):
        from rsconf.component import nginx

        jc = self.j2_ctx
        z = jc[self.name]
        nginx.install_vhost(self, vhost=z.vhost, j2_ctx=jc)
        systemd.docker_unit_enable(
            self,
            jc,
            image=z.docker_image,
            # TODO(e-carlin): This is the default command (set by build_docker_cmd)
            # is there a way to just use it and not specify cmd?
            ports=(
                (jc.nginx.docker_index_port, 8080),
                (jc.nginx.docker_flask_port, 8082),
            ),
        )
        self.install_access(mode="700", owner=z._run_u)
        self.install_directory(d)
