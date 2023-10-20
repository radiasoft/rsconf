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

_WORK_SUBDIR = "work"
_RUN_LOG = "00_rsaccounting_log.txt"
#: implicit directory name used by rclone relative to $XDG_CONFIG_HOME
_RCLONE_SUBDIR = "rclone"
_RCLONE_CONF_F = "rsaccounting_rclone.conf"
_GOOGLE_JSON_F = "rsaccounting_google.json"
_PASSWD_SECRET_F = "rsaccounting_auth"


class T(component.T):
    def internal_build_compile(self):
        from rsconf.component import nginx
        from rsconf.component import docker_registry

        self.buildt.require_component("network", "docker", "nginx")
        jc, z = self.j2_ctx_init()
        z._run_u = jc.rsconf_db.run_u
        self.__run_d = systemd.docker_unit_prepare(
            self,
            jc,
            # POSIT: _WORK_SUBDIR has no spaces or specials
            docker_exec=f"bash -c 'cd {_WORK_SUBDIR} && rsaccounting service start'",
        )
        z._xdg_config_home = self.__run_d
        z._rclone_d = z._xdg_config_home.join(_RCLONE_SUBDIR)
        z._work_d = self.__run_d.join(_WORK_SUBDIR)
        # POSIT: same as name inside _RCLONE_CONF_F
        z.pksetdefault(
            _auth_f=nginx.CONF_D.join(_PASSWD_SECRET_F),
            docker_image_is_local=False,
            rclone_remote=self.name,
            team_drive="Accounting",
            test_run_curr="",
            test_run_prev="",
        ).pksetdefault(
            docker_image=docker_registry.absolute_image(
                self,
                image=z.docker_image,
                image_is_local=z.docker_image_is_local,
            ),
        )
        self.j2_ctx_pykern_defaults()
        z._run_log = z._work_d.join(_RUN_LOG)
        z._run_monthly_f = self.__run_d.join("run-monthly")
        jc.pknested_set("pykern.pkasyncio.server_port", z.port)
        z.pknested_set("pkcli.service.monthly_cmd", z._run_monthly_f)

    def internal_build_write(self):
        from rsconf.component import nginx

        # TODO(robnagler) simplify in component.python_service_env
        def _env():
            return self.python_service_env(
                exclude_re="__|^rsaccounting_(?:docker|port|rclone|team|test|vhost)",
                values=PKDict(
                    (k, v)
                    for k, v in self.j2_ctx.items()
                    if k in ("rsaccounting", "pykern")
                ),
            )

        jc = self.j2_ctx
        z = jc[self.name]
        nginx.install_vhost(self, vhost=z.vhost, j2_ctx=jc)
        nginx.install_auth(
            self,
            _PASSWD_SECRET_F,
            jc.rsaccounting._auth_f,
            db.VISIBILITY_DEFAULT,
            jc,
        )
        jc.systemd.run_d
        systemd.docker_unit_enable(
            self,
            jc,
            image=z.docker_image,
            env=_env(),
        )
        self.install_access(mode="700", owner=z._run_u)
        # POSIT: xdg_config_home same as run_d so don't need to mkdir
        self.install_directory(z._rclone_d)
        self.install_directory(z._work_d)
        self.install_access(mode="500")
        self.install_resource(
            "rsaccounting/run-monthly",
            jc,
            z._run_monthly_f,
        )
        self.install_access(mode="400")
        self.install_abspath(
            db.secret_path(jc, _RCLONE_CONF_F),
            z._rclone_d.join("rclone.conf"),
        )
        self.install_abspath(
            db.secret_path(jc, _GOOGLE_JSON_F),
            # POSIT name is same inside rclone.conf
            z._rclone_d.join(_GOOGLE_JSON_F),
        )
