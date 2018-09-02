# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from rsconf import component


_CONF_F = 'conf.py'
_COOKIE_SECRET = 'jupyterhub_cookie_secret'
_PROXY_AUTH = 'jupyterhub_proxy_auth'
_USER_SUBDIR = 'user'


class T(component.T):
    def internal_build(self):
        from rsconf import db
        from rsconf import systemd
        from rsconf.component import docker
        from rsconf.component import docker_registry

        self.buildt.require_component('docker')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.jupyterhub
        z.vhost = j2_ctx.jupyterhub.vhosts[j2_ctx.rsconf_db.host]
        run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.update(
            user_d=run_d.join(_USER_SUBDIR),
            jupyter_docker_image=docker_registry.absolute_image(
                j2_ctx, z.jupyter_docker_image,
            ),
            run_u=j2_ctx.rsconf_db.root_u,
            jupyter_run_u=j2_ctx.rsconf_db.run_u,
        )
        z.home_d = db.user_home_path(j2_ctx, z.jupyter_run_u)
        self.install_access(mode='711', owner=z.run_u)
        self.install_directory(run_d)
        self.install_access(mode='700', owner=z.jupyter_run_u)
        self.install_directory(z.user_d)
        self.install_access(mode='400', owner=z.run_u)
        z.cookie_secret_hex = self.secret_path_value(
            _COOKIE_SECRET,
            gen_secret=lambda: db.random_string(length=256, is_hex=True),
            visibility='channel',
        )[0]
        z.proxy_auth_token = self.secret_path_value(
            _PROXY_AUTH,
            gen_secret=lambda: db.random_string(length=64, is_hex=True),
            visibility='channel',
        )[0]
        z.admin_users_str = "'" + "','".join(z.admin_users) + "'"
        conf_f = run_d.join(_CONF_F)
        self.install_resource('jupyterhub/{}'.format(_CONF_F), j2_ctx, conf_f)
        self.append_root_bash(
            "rsconf_service_docker_pull '{}'".format(z.jupyter_docker_image),
        )
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            cmd='jupyterhub -f {}'.format(conf_f),
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            ports=[int(z.port)],
            run_u=z.run_u,
            volumes=[docker.DOCKER_SOCK],
        )
