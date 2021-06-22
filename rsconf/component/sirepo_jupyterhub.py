# -*- coding: utf-8 -*-
u"""JupyterHub under Sirepo configuration

:copyright: Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkjson, pkio, pkconfig
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
import rsconf.component.jupyterhub

class T(rsconf.component.jupyterhub.T):
    _COOKIE_SECRET = 'sirepo_jupyterhub_cookie_secret'
    _PROXY_AUTH = 'sirepo_jupyterhub_proxy_auth'

    def internal_build_compile(self):
        # TODO(e-carlin): should this come from somewhere or ok to hardcode?
        self.__jupyterhub_run_d = pkio.py_path('/srv/jupyterhub')
        super().internal_build_compile()

    def sirepo_config(self, sirepo):
        self.j2_ctx_pksetdefault(sirepo.j2_ctx)
        sirepo.j2_ctx.sirepo_jupyterhub.hub_ip = self.j2_ctx.sirepo_jupyterhub.hub_ip

    def _auth(self, z):
        pass

    def _enable_docker(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        def _env_ok(elem):
            for p in (
                # TODO(e-carlin): all of auth and smtp is really too much.
                # We just need auth_methods for checking if the cookies is
                # valid. But bringing in methods then initializes the methods
                # so we have to bring in their full config.
                'SIREPO_AUTH',
                'SIREPO_COOKIE',
                'SIREPO_SIM_API_JUPYTERHUBLOGIN',
                'SIREPO_SMTP',
                'SIREPO_SRDB',
            ):
                if elem[0].startswith(f'{p}'):
                    return True
            return False


        z = self.j2_ctx[self.name]
        systemd.docker_unit_enable(
            self,
            self.j2_ctx,
            cmd="bash -l -c 'jupyterhub -f {}'".format(self.__conf_f),
            env=PKDict(
                filter(
                    _env_ok,
                    self.buildt.get_component('sirepo').sirepo_unit_env(self).items(),
                ),
                **pkconfig.to_environ(
                    ['*'],
                    values=dict(sirepo=dict(
                        feature_config=dict(sim_types=set(('jupyterhublogin',))),
                    )),
                ),
            ),
            image=docker_registry.absolute_image(self.j2_ctx, z.docker_image),
            run_u=z.run_u,
            volumes=[
                self._jupyterhub_db(),
                self.j2_ctx.sirepo.srdb.root,
            ],
        )

    def _install_jupyterhub_db(self, z):
        self.install_access(mode='711', owner=z.run_u)
        self.install_directory(self.__jupyterhub_run_d)

    def _jupyterhub_db(self):
        return self.__jupyterhub_run_d

    def _vhost(self, z, jc):
        pass


def _list_to_str(v):
    return "'" + "','".join(v) + "'"
