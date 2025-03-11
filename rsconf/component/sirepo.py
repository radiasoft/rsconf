"""create sirepo configuration

:copyright: Copyright (c) 2017-2023 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern import pkcompat
from pykern import pkconfig
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from rsconf import systemd
import base64
import os


_DB_SUBDIR = "db"

_USER_SUBDIR = "user"

_PROPRIETARY_CODE_SUBDIR = "proprietary_code"

#: secret basename
_COOKIE_PRIVATE_KEY = "sirepo_cookie_private_key"

#: secret basename
_SERVER_SECRET = "sirepo_job_server_secret"


class T(component.T):
    def internal_build_compile(self):
        from rsconf.component import docker_registry
        from rsconf import db

        def _defaults_1(jc):
            self.j2_ctx_pksetdefault(
                PKDict(
                    sirepo=PKDict(
                        cookie=PKDict(
                            http_name=lambda: "sirepo_{}".format(jc.rsconf_db.channel),
                            private_key=lambda: self.secret_path_value(
                                _COOKIE_PRIVATE_KEY,
                                gen_secret=lambda: pkcompat.from_bytes(
                                    base64.urlsafe_b64encode(os.urandom(32)),
                                ),
                                visibility="channel",
                            )[0],
                        ),
                        docker_image=docker_registry.absolute_image(self),
                        feature_config=PKDict(
                            api_modules=[],
                            default_proprietary_sim_types=tuple(),
                            moderated_sim_types=tuple(),
                            proprietary_sim_types=tuple(),
                            proprietary_code_tarballs=tuple(),
                        ),
                        job=PKDict(
                            max_message_bytes="200m",
                        ),
                        pkcli=PKDict(
                            service=PKDict(
                                ip=db.LOCAL_IP,
                                run_dir=self.__run_d,
                            ),
                        ),
                        srdb=PKDict(root=self.__run_d.join(_DB_SUBDIR)),
                        static_files_expires="1d",
                        wordpress_host=None,
                    ),
                )
            )
            self.j2_ctx_pykern_defaults()

        def _defaults_2(jc):
            self.j2_ctx_pksetdefault(
                PKDict(
                    sirepo=PKDict(
                        client_max_body_size=pkconfig.parse_bytes(
                            jc.sirepo.job.max_message_bytes
                        ),
                        job_api=PKDict,
                        job_driver=PKDict(modules=["docker"]),
                        job=PKDict(
                            server_secret=lambda: self.secret_path_value(
                                _SERVER_SECRET,
                                gen_secret=lambda: pkcompat.from_bytes(
                                    base64.urlsafe_b64encode(os.urandom(32)),
                                ),
                                visibility="channel",
                            )[0],
                            verify_tls=lambda: jc.rsconf_db.channel != "dev",
                        ),
                        pkcli=PKDict(
                            job_supervisor=PKDict(
                                ip=db.LOCAL_IP,
                                port=8001,
                            ),
                        ),
                    ),
                )
            )

        def _tornado(jc, z):
            z._first_port = int(z.pknested_get("pkcli.service_port"))
            z._last_port = z._first_port + int(z.num_api_servers) - 1
            assert z._first_port <= z._last_port
            z.pkcli_service_tornado_primary_port = z._first_port
            self.__instance_spec = systemd.InstanceSpec(
                base=self.name,
                env_var="SIREPO_PKCLI_SERVICE_PORT",
                first_port=z._first_port,
                last_port=z._last_port,
            )
            self.__run_d = systemd.docker_unit_prepare(
                self,
                jc,
                instance_spec=self.__instance_spec,
                docker_exec="sirepo service tornado",
            )
            self.__static_files_gen_f = self.__run_d.join("static_files_gen")

        self.__env_components = ["sirepo", "pykern"]
        self.__docker_unit_enable_after = []
        self.__docker_vols = []
        self.buildt.require_component("docker", "nginx", "db_bkp")
        jc, z = self.j2_ctx_init()
        _tornado(jc, z)
        z._run_u = jc.rsconf_db.run_u
        _defaults_1(jc)
        self._raydata()
        self._jupyterhublogin(z)
        # Must come before sirepo_job_supervisor. This sets config that supervisor needs.
        self._viz3d()
        _defaults_2(jc)
        # server connects locally only so go direct to tornado.
        # supervisor has different uri to pass to agents.
        z.job_api.supervisor_uri = "http://{}:{}".format(
            z.pkcli.job_supervisor.ip,
            z.pkcli.job_supervisor.port,
        )
        self._set_sirepo_config("sirepo_job_supervisor")

    def internal_build_write(self):
        from rsconf.component import db_bkp
        from rsconf.component import nginx
        from rsconf.component import docker

        def _tornado(jc, z):
            nginx.install_vhost(
                self,
                vhost=z.vhost,
                resource_f="sirepo/tornado_nginx.conf",
                j2_ctx=jc,
            )
            systemd.docker_unit_enable(
                self,
                jc,
                image=z.docker_image,
                env=self.sirepo_unit_env(self, exclude_re="^(?:sirepo_job_driver)"),
                after=self.__docker_unit_enable_after,
                volumes=self.__docker_vols,
                static_files_gen=self.__static_files_gen_f,
            )

        jc = self.j2_ctx
        z = jc[self.name]
        self._install_dirs_and_files()
        _tornado(jc, z)
        db_bkp.install_script_and_subdir(
            self,
            jc,
            run_u=z._run_u,
            run_d=self.__run_d,
        )

    def sirepo_unit_env(self, compt, exclude_re=None):
        # Only variable that is required to be in the environment
        return self.python_service_env(
            values=PKDict(
                (k, v) for k, v in compt.j2_ctx.items() if k in self.__env_components
            ),
            # local only values; exclude double under (__) which are "private" values, e.g. sirepo._run_u
            exclude_re=r"^sirepo(?:_docker_image|_static_files|.*_vhost|.*_client_max_body|_num_api_servers|__|_raydata)"
            + ("|" + exclude_re if exclude_re else ""),
        )

    def _install_dirs_and_files(self):
        from rsconf.component import nginx

        jc = self.j2_ctx
        z = jc[self.name]
        self.install_access(mode="700", owner=z._run_u)
        self.install_directory(self.__run_d)
        d = self.__run_d.join(_DB_SUBDIR)
        self.install_directory(d)
        self.install_directory(d.join(_USER_SUBDIR))
        if self.__static_files_gen_f:
            z._static_files_nginx_d = nginx.STATIC_FILES_ROOT_D.join(self.name)
            z._static_files_gen_d = self.__run_d.join("static_files_gen_tmp")
            self.install_access(mode="500")
            self.install_resource(
                "sirepo/static_files_gen.sh",
                jc,
                self.__static_files_gen_f,
            )
            self.install_access(mode="700")
        if not z.feature_config.proprietary_code_tarballs:
            return
        p = d.join(_PROPRIETARY_CODE_SUBDIR)
        self.install_directory(p)
        for c in z.feature_config.proprietary_code_tarballs:
            self.install_directory(p.join(c))
        self.install_access(mode="400")
        for c in z.feature_config.proprietary_code_tarballs:
            self.install_abspath(
                self.proprietary_file(jc, c),
                p.join(c, c + ".tar.gz"),
            )

    def _jupyterhublogin(self, z):
        z.jupyterhub_enabled = self._in_sim_types("jupyterhublogin")
        if not z.jupyterhub_enabled:
            return
        self.__docker_vols.append(z.sim_api.jupyterhublogin.user_db_root_d)
        self._set_sirepo_config("sirepo_jupyterhub")

    def _raydata(self):
        if self._in_sim_types("raydata"):
            self._set_sirepo_config("raydata_scan_monitor")

    def _set_sirepo_config(self, component, is_docker_component=True):
        self.buildt.require_component(component)
        c = self.buildt.get_component(component)
        c.sirepo_config(self)
        if is_docker_component:
            self.__docker_unit_enable_after.append(c.name)

    def _in_sim_types(self, to_check):
        for k, v in self.j2_ctx.sirepo.feature_config.items():
            if "sim_types" in k and to_check in v:
                return True
        return False

    def _viz3d(self):
        if (
            self.j2_ctx.sirepo.feature_config.get("enable_global_resources", False)
            and "viz3d" in self.j2_ctx.sirepo.feature_config.proprietary_sim_types
        ):
            n = self.buildt.get_component("network")
            n.add_public_tcp_ports(
                list(
                    range(
                        self.j2_ctx.sirepo.global_resources.public_ports_min,
                        self.j2_ctx.sirepo.global_resources.public_ports_max,
                    )
                )
            )
            self._set_sirepo_config("rsiviz", is_docker_component=False)
            self.__env_components += ["rsiviz"]
