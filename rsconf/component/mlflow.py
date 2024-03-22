"""MLFlow tracking server

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern import pkconfig
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component


_DB_SUBDIR = "db"
_BASIC_AUTH_CONF_F = "basic-auth.ini"
_BASIC_AUTH_DB_F = "basic-auth.db"
_SECRETS = {"mlflow_admin_password", "mlflow_admin_username"}


class T(component.T):
    def internal_build_compile(self):
        from rsconf import db
        from rsconf import systemd

        self.buildt.require_component("docker", "network")
        jc, z = self.j2_ctx_init()
        z.run_d = systemd.unit_run_d(jc, self.name)
        z.db_d = z.run_d.join(_DB_SUBDIR)
        z.auth_conf_f = z.run_d.join(_BASIC_AUTH_CONF_F)
        z.auth_db_f = z.run_d.join(_BASIC_AUTH_DB_F)
        z.mlflow_ip = db.LOCAL_IP
        systemd.docker_unit_prepare(
            self,
            jc,
            docker_exec=f"mlflow server --host {z.mlflow_ip} --port {z.service_port} --backend-store-uri 'sqlite:///{z.db_d}/backend-store.db' --no-serve-artifacts --default-artifact-root '{z.db_d}' --app-name basic-auth",
        )
        for s in _SECRETS:
            z[s] = self.secret_path_value(
                s,
                gen_secret=lambda: db.random_string(length=16),
                visibility="host",
            )[0]

    def internal_build_write(self):
        from rsconf import systemd
        from rsconf.component import docker_registry
        from rsconf.component import nginx

        jc = self.j2_ctx
        z = jc[self.name]
        systemd.docker_unit_enable(
            self,
            jc,
            env=self.python_service_env(
                values=PKDict(mlflow_auth_config_path=z.auth_conf_f)
            ),
            image=docker_registry.absolute_image(self),
            volumes=[z.db_d],
        )
        self.install_access(mode="700", owner=jc.rsconf_db.run_u)
        self.install_directory(z.db_d)
        self.install_resource2(_BASIC_AUTH_CONF_F, z.auth_conf_f.dirname, access="400")
        nginx.install_vhost(
            self,
            vhost=z.vhost,
            backend_host=z.mlflow_ip,
            backend_port=z.service_port,
            j2_ctx=jc,
        )
