# -*- coding: utf-8 -*-
u"""create docker configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio

DOCKER_SOCK = '/var/run/docker.sock'

_CONF_DIR = pkio.py_path('/etc/docker')
_TLS_DIR = _CONF_DIR.join('tls')
_DAEMON_JSON = _CONF_DIR.join('daemon.json')
_ROOT_CONFIG_JSON = pkio.py_path('/root/.docker/config.json')
_TLS_BASENAME = 'docker_tls'


class T(component.T):
    def internal_build(self):
        from rsconf.component import docker_registry
        from rsconf.component import docker_cache
        from rsconf.component import db_bkp
        from rsconf import systemd

        self.buildt.require_component('base_all', 'db_bkp')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.docker
        systemd.unit_prepare(self, j2_ctx, [_CONF_DIR])
        z.run_d = systemd.unit_run_d(j2_ctx, 'docker')
        z.data_d = z.run_d
        z.run_u = j2_ctx.rsconf_db.root_u
        docker_registry.update_j2_ctx(j2_ctx)
        docker_cache.update_j2_ctx(j2_ctx)
        self.install_access(mode='700', owner=z.run_u)
        self.install_directory(_CONF_DIR)
        if 'tls_host' in z:
            self._setup_tls_host(j2_ctx, z)
        self.install_access(mode='400')
        self.install_resource(
            'docker/daemon.json',
            j2_ctx,
            _DAEMON_JSON,
        )
        self.append_root_bash_with_main(j2_ctx)
        j2_ctx.docker.setdefault('auths', pkcollections.Dict())
        # Must be after everything else related to daemon
        docker_registry.install_crt_and_login(self, j2_ctx)
        docker_cache.install_crt(self, j2_ctx)
        j2_ctx.docker.config_login = dict(
            detachKeys='ctrl-],q',
        )
        if j2_ctx.docker.auths:
            j2_ctx.docker.config_login['auths'] = _dict(j2_ctx.docker.auths)
        self.install_access(mode='700', owner=z.run_u)
        self.install_directory(_ROOT_CONFIG_JSON.dirname)
        self.install_access(mode='400')
        self.install_resource(
            'docker/root_config.json',
            j2_ctx,
            _ROOT_CONFIG_JSON,
        )
        systemd.unit_enable(self, j2_ctx)
        self.rsconf_service_restart()
        db_bkp.install_script_and_subdir(
            self,
            j2_ctx,
            run_u=z.run_u,
            run_d=z.run_d,
        )

    def _self_signed_crt(self, j2_ctx):
        from rsconf.pkcli import tls
        from rsconf import db

        b = db.secret_path(j2_ctx, _TLS_BASENAME, visibility='host')
        res = pkcollections.Dict(
            key=b + tls.KEY_EXT,
            crt=b + tls.CRT_EXT,
        )
        if not res.crt.check():
            pkio.mkdir_parent_only(res.crt)
            tls.gen_self_signed_crt(str(b), j2_ctx.rsconf_db.host)
        return res


    def _setup_tls_host(self, j2_ctx, z):
        import socket

        c = self._self_signed_crt(j2_ctx)
        self.install_access(mode='700', owner=z.run_u)
        self.install_directory(_TLS_DIR)
        self.install_access(mode='400', owner=z.run_u)
        z.tls = pkcollections.Dict()
        for k in 'crt', 'key':
            z.tls[k] = _TLS_DIR.join(c[k].basename)
            self.install_abspath(c[k], z.tls[k])
        z.tls.ip = socket.gethostbyname(z.tls_host)


def _dict(value):
    # may be pkcollections.Dict which is subclass of dict
    if not isinstance(value, dict):
        return value
    res = {}
    for k, v in value.items():
        res[k] = _dict(v)
    return res
