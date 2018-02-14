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
        self.install_resource(
            'docker/daemon.json',
            j2_ctx,
            _DAEMON_JSON,
        )
        self.append_root_bash_with_main(j2_ctx)
        # Must be after everything else
        docker_registry.install_crt_and_login(self, j2_ctx)
        #TODO(robnagler) thin pool creation one command, fixed size unless dev
        #TODO(robnagler) add live-restore?
        # live restore: https://docs.docker.com/engine/admin/live-restore
        # "live-restore": true,
        # live-restore does interrupt network due to proxies, --net=host
