# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkjson
from rsconf import component


_CONF_F = 'conf.py'
_COOKIE_SECRET = 'jupyterhub_cookie_secret'
_PROXY_AUTH = 'jupyterhub_proxy_auth'
_USER_SUBDIR = 'user'
_DOCKER_TLS_SUBDIR = 'docker_tls'
_DEFAULT_PORT_BASE = 8800
# POSIT: rsdockerspawner._DEFAULT_POOL_NAME
_DEFAULT_POOL_NAME = 'default'


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
        z.run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.update(
            user_d=z.run_d.join(_USER_SUBDIR),
            jupyter_docker_image=docker_registry.absolute_image(
                j2_ctx, z.jupyter_docker_image,
            ),
            run_u=j2_ctx.rsconf_db.root_u,
            jupyter_run_u=j2_ctx.rsconf_db.run_u,
        )
        z.home_d = db.user_home_path(j2_ctx, z.jupyter_run_u)
        self.install_access(mode='711', owner=z.run_u)
        self.install_directory(z.run_d)
        self.install_access(mode='700', owner=z.jupyter_run_u)
        self.install_directory(z.user_d)
        self.install_access(mode='400', owner=z.run_u)
        z.cookie_secret_hex = self.secret_path_value(
            _COOKIE_SECRET,
            gen_secret=lambda: db.random_string(length=64, is_hex=True),
            visibility='channel',
        )[0]
        z.proxy_auth_token = self.secret_path_value(
            _PROXY_AUTH,
            gen_secret=lambda: db.random_string(length=64, is_hex=True),
            visibility='channel',
        )[0]
        z.admin_users_str = _list_to_str(z.admin_users)
        if z.get('whitelist_users'):
            # admin_users are implicitly part of whitelist
            z.whitelist_users_str = _list_to_str(z.whitelist_users)
        if z.get('pools'):
            self._rsdockerspawner(j2_ctx, z)
        conf_f = z.run_d.join(_CONF_F)
        self.install_resource('jupyterhub/{}'.format(_CONF_F), j2_ctx, conf_f)
        self.append_root_bash(
            "rsconf_service_docker_pull '{}'".format(z.jupyter_docker_image),
        )
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            cmd='jupyterhub -f {}'.format(conf_f),
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
#            ports=[int(z.port)],
            run_u=z.run_u,
            volumes=[docker.DOCKER_SOCK],
        )

    def _rsdockerspawner(self, j2_ctx, z):
        from rsconf.component import docker

        tls_d = z.run_d.join(_DOCKER_TLS_SUBDIR)
        c = pkcollections.Dict(
            port_base=z.setdefault('port_base', _DEFAULT_PORT_BASE),
            tls_dir=str(tls_d),
        )
        seen = pkcollections.Dict(
            hosts=pkcollections.Dict(),
            users=pkcollections.Dict(),
        )
        for n, p in z.pools.items():
            p.setdefault('users', [])
            assert p.users or n == _DEFAULT_POOL_NAME, \
                'no users in pool={}'.format(n)
            assert p.setdefault('servers_per_host', 0) >= 1, \
                'invalid servers_per_host={} in pool={}'.format(
                    p.servers_per_host,
                    n,
                )
            for x in 'hosts', 'users':
                for y in p[x]:
                    assert y not in seen[x], \
                        'duplicate value={} in {} pool={}'.format(y, x, n)
                    seen[x][y] = n
            p.setdefault('mem_limit', None)
            p.setdefault('cpu_limit', None)
        c.pools = z.pools
        docker.setup_cluster(
            self,
            hosts=seen.hosts.keys(),
            tls_d=tls_d,
            run_u=z.run_u,
            j2_ctx=j2_ctx,
        )
        z.rsdockerspawner_cfg = pkjson.dump_pretty(c)


def _list_to_str(v):
    return "'" + "','".join(v) + "'"
