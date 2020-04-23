# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from pykern import pkcollections
from pykern import pkjson
from rsconf import component


_CONF_F = 'conf.py'
_TEMPLATE_D = 'template'
_COOKIE_SECRET = 'jupyterhub_cookie_secret'
_PROXY_AUTH = 'jupyterhub_proxy_auth'
_USER_SUBDIR = 'user'
_DOCKER_TLS_SUBDIR = 'docker_tls'
_DEFAULT_PORT_BASE = 8100
# POSIT: rsdockerspawner._DEFAULT_POOL_NAME
_DEFAULT_USER_GROUP = 'everybody'
_DEFAULT_POOL_V3 = _DEFAULT_USER_GROUP
_DEFAULT_MOCK_PASSWORD = 'testpass'


class T(component.T):
    def internal_build_compile(self):
        from rsconf import db
        from rsconf import systemd
        from rsconf.component import docker_registry

        self.buildt.require_component('docker', 'network')
        jc = self.jc = self.hdb.j2_ctx_copy()
        z = jc.jupyterhub
        z.vhost = jc.jupyterhub.vhosts[jc.rsconf_db.host]
        z.run_d = systemd.docker_unit_prepare(self, jc)
        z.update(
            user_d=z.run_d.join(_USER_SUBDIR),
            jupyter_docker_image=docker_registry.absolute_image(
                jc, z.jupyter_docker_image,
            ),
            run_u=jc.rsconf_db.get('run_u'),
            jupyter_run_u=jc.rsconf_db.run_u,
        )
        z.setdefault('http_timeout', 30);
        z.setdefault('template_vars', {});
        nc = self.buildt.get_component('network')
        z.hub_ip = nc.ip_and_net_for_host(jc.rsconf_db.host)[0]
        z.template_d = z.run_d.join(_TEMPLATE_D)
        z.home_d = db.user_home_path(jc, z.jupyter_run_u)
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
        self._rsdockerspawner(jc, z)

    def internal_build_write(self):
        from rsconf import db
        from rsconf import systemd
        from rsconf.component import docker_registry
        from rsconf.component import docker

        z = self.jc.jupyterhub
        self.install_access(mode='711', owner=z.run_u)
        self.install_directory(z.run_d)
        self.install_access(mode='700', owner=z.jupyter_run_u)
        self.install_directory(z.user_d)
        self.install_directory(z.template_d)
        self.install_access(mode='400', owner=z.run_u)
        docker.setup_cluster(
            self,
            hosts=z.docker_hosts,
            tls_d=z.tls_d,
            run_u=z.run_u,
            j2_ctx=self.jc,
        )
        if self.jc.rsconf_db.channel == 'dev':
            z.setdefault('mock_password', _DEFAULT_MOCK_PASSWORD)
        else:
            g = z.get('github')
            assert g and g.get('client_id') and g.get('client_secret'), \
                'jupyter.github={} client_id/secret not set'.format(g)
        conf_f = z.run_d.join(_CONF_F)
        self.install_resource('jupyterhub/{}'.format(_CONF_F), self.jc, conf_f)
        self.append_root_bash(
            "rsconf_service_docker_pull '{}'".format(z.jupyter_docker_image),
        )
        kw = pkcollections.Dict()
        kw.ports = [int(z.port)]
        kw.volumes = [docker.DOCKER_SOCK]
        systemd.docker_unit_enable(
            self,
            self.jc,
            cmd="bash -l -c 'jupyterhub -f {}'".format(conf_f),
            image=docker_registry.absolute_image(self.jc, z.docker_image),
            run_u=z.run_u,
            **kw
        )

    def _rsdockerspawner(self, j2_ctx, z):
        from rsconf.component import docker

        z.tls_d = z.run_d.join(_DOCKER_TLS_SUBDIR)
        c = pkcollections.Dict(
            port_base=z.setdefault('port_base', _DEFAULT_PORT_BASE),
            tls_dir=str(z.tls_d),
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
        self._rsdockerspawner_v3(j2_ctx, z, seen)
        c.user_groups = z.get('user_groups', PKDict())
        c.volumes = z.volumes
        c.pools = z.pools
        z.rsdockerspawner_cfg = pkjson.dump_pretty(c)
        z.docker_hosts = list(seen.hosts.keys())

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
                    'user_groups may not be specified for pool={}'.format(n)
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
