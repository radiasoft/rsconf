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
_PORTS = PKDict(
    index_port=8880,
    flask_port=8882,
)


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("docker", "nginx")
        jc, z = self.j2_ctx_init()
        z._run_u = jc.rsconf_db.run_u
        self.j2_ctx_pkupdate(
            PKDict(
                nginx=PKDict(
                    docker_index_port=z.index_iframe_port,
                    docker_flask_port=z.server_port,
                    **_PORTS,
                ),
                pykern=PKDict(
                    pkconfig=PKDict(channel=jc.rsconf_db.channel),
                    pkasyncio=PKDict(server_port=z.server_port),
                ),
                rsiviz=PKDict(
                    pkcli=PKDict(service=PKDict(index_iframe_port=z.index_iframe_port))
                ),
            ),
        )
        self.__run_d = systemd.docker_unit_prepare(
            self,
            jc,
            # TODO(e-carlin): This is the default command (set by build_docker_cmd)
            # is there a way to just use it and not specify cmd?
            docker_exec=f"bash {db.user_home_path(z._run_u)}/.radia-run/start",
        )

    def internal_build_write(self):
        from rsconf.component import nginx

        jc = self.j2_ctx
        z = jc[self.name]
        d = self.__run_d.join(_DB_SUBDIR)
        nginx.install_vhost(
            self,
            vhost=self.hdb.rsconf_db.host,
            j2_ctx=jc,
        )
        e = PKDict(rsiviz=z, pykern=jc.pykern)
        if "dice" in z:
            e.dice = z.dice
        systemd.docker_unit_enable(
            self,
            jc,
            env=self.python_service_env(
                e,
                exclude_re=r"^rsiviz(?:__|_docker_image|_url_secret|_dice_)",
            ),
            image=z.docker_image,
        )
        self.install_access(mode="700", owner=z._run_u)
        self.install_directory(d)
