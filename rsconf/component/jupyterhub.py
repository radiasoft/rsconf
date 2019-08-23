# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdp
from pykern import pkcollections
from pykern import pkjson
from rsconf import component


_CONF_F = 'conf.py'
_COOKIE_SECRET = 'jupyterhub_cookie_secret'
_PROXY_AUTH = 'jupyterhub_proxy_auth'
_USER_SUBDIR = 'user'
_DOCKER_TLS_SUBDIR = 'docker_tls'
_DEFAULT_PORT_BASE = 8100
# POSIT: rsdockerspawner._DEFAULT_POOL_NAME
_DEFAULT_POOL_V2 = 'default'
_DEFAULT_USER_GROUP = 'everybody'
_DEFAULT_POOL_V3 = _DEFAULT_USER_GROUP
_DEFAULT_MOCK_PASSWORD = 'testpass'


class T(component.T):
    def internal_build(self):
        from rsconf import db
        from rsconf import systemd
        from rsconf.component import docker
        from rsconf.component import docker_registry

        self.buildt.require_component('docker')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.jupyterhub
        rsd = bool(z.get('pools'))
        z.vhost = j2_ctx.jupyterhub.vhosts[j2_ctx.rsconf_db.host]
        z.setdefault('http_timeout', 30);
        z.run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.update(
            user_d=z.run_d.join(_USER_SUBDIR),
            jupyter_docker_image=docker_registry.absolute_image(
                j2_ctx, z.jupyter_docker_image,
            ),
            run_u=j2_ctx.rsconf_db.get('run_u' if rsd else 'root_u'),
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
        # deprecated but does not conflict so leave
        if z.get('whitelist_users'):
            # admin_users are implicitly part of whitelist
            z.whitelist_users_str = _list_to_str(z.whitelist_users)
        if rsd:
            self._rsdockerspawner(j2_ctx, z)
        if j2_ctx.rsconf_db.channel == 'dev':
            z.setdefault('mock_password', _DEFAULT_MOCK_PASSWORD)
        else:
            g = z.get('github')
            assert g and g.get('client_id') and g.get('client_secret'), \
                'jupyter.github={} client_id/secret not set'.format(g)
        conf_f = z.run_d.join(_CONF_F)
        self.install_resource('jupyterhub/{}'.format(_CONF_F), j2_ctx, conf_f)
        self.append_root_bash(
            "rsconf_service_docker_pull '{}'".format(z.jupyter_docker_image),
        )
        kw = pkcollections.Dict()
        if not rsd:
            kw.ports = [int(z.port)]
            kw.volumes = [docker.DOCKER_SOCK]
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            cmd='jupyterhub -f {}'.format(conf_f),
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            run_u=z.run_u,
            **kw
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
        # POSIT: notebook_dir in
        # radiasoft/container-beamsim-jupyter/container-conf/build.sh
        # parameterize anyway, because matches above
        z.setdefault('volumes', pkcollections.Dict())
        z.volumes.setdefault(
            str(z.user_d.join('{username}')),
            pkcollections.Dict(bind=str(z.home_d.join('jupyter'))),
        )
        if z.get('user_groups'):
            self._rsdockerspawner_v3(j2_ctx, z, seen)
            c.user_groups = z.user_groups
        else:
            self._rsdockerspawner_v2_deprecated(j2_ctx, z, seen)
        docker.setup_cluster(
            self,
            hosts=seen.hosts.keys(),
            tls_d=tls_d,
            run_u=z.run_u,
            j2_ctx=j2_ctx,
        )
        c.volumes = z.volumes
        c.pools = z.pools
        z.rsdockerspawner_cfg = pkjson.dump_pretty(c)

    def _rsdockerspawner_v2_deprecated(self, j2_ctx, z, seen):
        for n, p in z.pools.items():
            if n == _DEFAULT_POOL_V2:
                p.setdefault('users', [])
            else:
                assert p.users, \
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
            p.setdefault('min_activity_hours', None)

    def _rsdockerspawner_v3(self, j2_ctx, z, seen):
        def _users_for_groups(groups, t, n):
            res = set()
            for g in groups:
                if g == _DEFAULT_USER_GROUP:
                    return []
                u = z.user_groups.get(g)
                assert u is not None, \
                    'user_group={} not found for {}={}'.format(g ,t, n)
                res.union(u)
            return sorted(res)

        for n, v in z.volumes.items():
            m = v.get('mode')
            if not isinstance(m, dict):
                continue
            seen2 = set()
            for g in m.values():
                for u in _users_for_groups(g, 'volume', n):
                    assert u not in seen2, \
                        'user={} in both modes for volume={}'.format(u, n)
                    seen2.add(u)
        for n, p in z.pools.items():
            for h in p['hosts']:
                assert h not in seen.hosts, \
                    'duplicate host={} in two pools {} and {}'.format(
                        h,
                        n,
                        seen.hosts[h],
                    )
                seen.hosts[h] = n
            if n == _DEFAULT_POOL_V3:
                assert 'user_groups' not in p, \
                    'user_groups may not be specifed for pool={}'.format(n)
            else:
                for u in _users_for_groups(p.user_groups, 'pool', n):
                    assert s not in seen.users, \
                        'duplicate user={} in two pools {} and {}'.format(
                            s,
                            n,
                            seen.hosts[s],
                        )
                    seen.users[s] = n


def _list_to_str(v):
    return "'" + "','".join(v) + "'"
