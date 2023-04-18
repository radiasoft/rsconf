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

_DB_SUBDIR = "db"


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("docker", "nginx")
        jc, z = self.j2_ctx_init()
        z._run_u = jc.rsconf_db.run_u
        self.__run_d = systemd.docker_unit_prepare(
            self,
            jc,
            docker_exec=f"bash {db.user_home_path(z._run_u)}/.radia-run/start",
        )

    def internal_build_write(self):
        from rsconf.component import db_bkp
        from rsconf.component import nginx
        from rsconf.component import docker

        jc = self.j2_ctx
        z = jc[self.name]
        d = self.__run_d.join(_DB_SUBDIR)
        jc.nginx.pkupdate(
            index_port=8880,
            flask_port=8882,
            docker_index_port=8000,
            docker_flask_port=8002,
        )
        nginx.install_vhost(
            self,
            vhost=self.hdb.rsconf_db.host,
            j2_ctx=jc,
        )
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
