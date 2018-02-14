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
_DAEMON_JSON = _CONF_DIR.join('daemon.json')
_ROOT_CONFIG_JSON = pkio.py_path('/root/.docker/config.json')


class T(component.T):
    def internal_build(self):
        from rsconf.component import docker_registry
        from rsconf import systemd

        self.buildt.require_component('base_all')
        systemd.unit_prepare(self, _CONF_DIR)
        j2_ctx = self.hdb.j2_ctx_copy()
        j2_ctx.docker.update(
            data_d=systemd.unit_run_d(j2_ctx, 'docker'),
        )
        docker_registry.update_j2_ctx(j2_ctx)
        self.install_access(mode='700', owner=j2_ctx.rsconf_db.root_u)
        self.install_directory(_CONF_DIR)
        self.install_access(mode='400', owner=j2_ctx.rsconf_db.root_u)
        # live restore: https://docs.docker.com/engine/admin/live-restore
        # live-restore does interrupt network due to proxies, --net=host
        self.install_resource(
            'docker/daemon.json',
            j2_ctx,
            _DAEMON_JSON,
        )
        self.append_root_bash_with_main(j2_ctx)
        j2_ctx.docker.setdefault('auths', pkcollections.Dict())
        j2_ctx.docker.auths
        # Must be after everything else related to daemon
        docker_registry.install_crt_and_login(self, j2_ctx)
        j2_ctx.docker.config_login = dict(
            detachKeys='ctrl-],q',
        )
        if j2_ctx.docker.auths:
            j2_ctx.docker.config_login['auths'] = _dict(j2_ctx.docker.auths)
        self.install_access(mode='700', owner=j2_ctx.rsconf_db.root_u)
        self.install_directory(_ROOT_CONFIG_JSON.dirname)
        self.install_access(mode='400', owner=j2_ctx.rsconf_db.root_u)
        self.install_resource(
            'docker/root_config.json',
            j2_ctx,
            _ROOT_CONFIG_JSON,
        )


def _dict(value):
    # may be pkcollections.Dict which is subclass of dict
    if not isinstance(value, dict):
        return value
    res = {}
    for k, v in value.items():
        res[k] = _dict(v)
    return res
