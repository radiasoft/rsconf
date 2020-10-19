# -*- coding: utf-8 -*-
u"""JupyterHub under Sirepo configuration

:copyright: Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkjson
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component

_COOKIE_SECRET = 'sirepo_jupyterhub_cookie_secret'
_CONF_F = 'conf.py'
_DEFAULT_PORT_BASE = 8100
# POSIT: rsdockerspawner._DEFAULT_POOL_NAME
_DEFAULT_USER_GROUP = 'everybody'
_DEFAULT_POOL_V3 = _DEFAULT_USER_GROUP
_DOCKER_TLS_SUBDIR = 'docker_tls'
_PROXY_AUTH = 'sirepo_jupyterhub_proxy_auth'
_TEMPLATE_D = 'template'
_USER_SUBDIR = 'user'


class T(component.T):

    def internal_build_compile(self):
        from rsconf import db
        from rsconf import systemd
        from rsconf.component import docker_registry

        self.buildt.require_component('docker')
        jc, z = self.j2_ctx_init()
        z.run_d = systemd.docker_unit_prepare(self, jc)
        z.update(
            # TODO(e-carlin): user_d needs to come from Sirepo
            # and be the sirepo.sim_api.jupterhublogin.dst_db_root
            user_d=z.run_d.join(_USER_SUBDIR),
            jupyter_docker_image=docker_registry.absolute_image(
                jc, z.jupyter_docker_image,
            ),
            run_u=jc.rsconf_db.run_u,
            jupyter_run_u=jc.rsconf_db.run_u,
        )
        z.setdefault('http_timeout', 30);
        z.setdefault('template_vars', {});
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
        self._rsdockerspawner(jc, z)

    def internal_build_write(self):
        from rsconf import db
        from rsconf import systemd
        from rsconf.component import docker
        from rsconf.component import docker_registry

        def _env_ok(k):
            for p in (
                    'SIREPO_AUTH',
                    'SIREPO_COOKIE',
                    'SIREPO_FEATURE_CONFIG_OTHER_SIM',
                    'SIREPO_SIM_API_JUPYTERHUBLOGIN',
                    'SIREPO_SRDB',
            ):
                if k.startswith(f'{p}_'):
                    return True
            return False

        jc = self.j2_ctx
        z = jc[self.name]
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
            j2_ctx=jc,
        )
        s = jc.sirepo
        if 'github' in s.auth.methods:
            g = s.auth.github
            assert g and g.get('key') and g.get('secret'), \
                'sirepo.auth.github={} key/secret not set'.format(g)
        conf_f = z.run_d.join(_CONF_F)
        self.install_resource('sirepo_jupyterhub/{}'.format(_CONF_F), jc, conf_f)
        self.append_root_bash(
            "rsconf_service_docker_pull '{}'".format(z.jupyter_docker_image),
        )
        e = PKDict()
        for k, v in self.buildt.get_component('sirepo').sirepo_unit_env(self).items():
            if _env_ok(k):
                e[k] = v
        systemd.docker_unit_enable(
            self,
            jc,
            cmd="bash -l -c 'jupyterhub -f {}'".format(conf_f),
            env=e,
            image=docker_registry.absolute_image(jc, z.docker_image),
            run_u=z.run_u,
            volumes=[jc.sirepo.srdb.root],
        )

    def sirepo_config(self, sirepo):
        self.j2_ctx_pksetdefault(sirepo.j2_ctx)

    def _rsdockerspawner(self, j2_ctx, z):
        from rsconf.component import docker

        z.tls_d = z.run_d.join(_DOCKER_TLS_SUBDIR)
        c = PKDict(
            port_base=z.setdefault('port_base', _DEFAULT_PORT_BASE),
            tls_dir=str(z.tls_d),
        )
        seen = PKDict(
            hosts=PKDict(),
            users=PKDict(),
        )
        # POSIT: notebook_dir in
        # radiasoft/container-beamsim-jupyter/container-conf/build.sh
        # parameterize anyway, because matches above
        z.setdefault('volumes', PKDict())
        z.volumes.setdefault(
            str(z.user_d.join('{username}')),
            PKDict(bind=str(z.home_d.join('jupyter'))),
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
                    assert u not in seen.users, \
                        'duplicate user={} in two pools {} and {}'.format(
                            u,
                            n,
                            seen.hosts[u],
                        )
                    seen.users[s] = n


def _list_to_str(v):
    return "'" + "','".join(v) + "'"
