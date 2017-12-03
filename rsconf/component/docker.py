# -*- coding: utf-8 -*-
u"""create docker configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio


_CONF_DIR = pkio.py_path('/etc/docker')
_DAEMON_JSON = _CONF_DIR.join('daemon.json')


class T(component.T):
    def internal_build(self):
        from rsconf.component import docker_registry

        self.buildt.require_component('base_users')
        #TODO(robnagler) if /etc/docker changes restart daemon
        #  coordinate with main.sh which may have just started daemon
        self.append_root_bash(
            "rsconf_service_prepare '{}' '{}'".format(
                self.name,
                _DAEMON_JSON,
            ),
        )
        j2_ctx = pkcollections.Dict(self.hdb)
        docker_registry.update_j2_ctx(j2_ctx)
        self.install_access(mode='700', owner=j2_ctx.rsconf_db_root_u)
        self.install_directory(_CONF_DIR)
        self.install_access(mode='400', owner=j2_ctx.rsconf_db_root_u)
        self.install_resource(
            'docker/daemon.json',
            j2_ctx,
            _DAEMON_JSON,
        )
        self.append_root_bash_with_resource(
            'docker/main.sh',
            j2_ctx,
            'docker_main',
        )
        # Must be after everything else
        docker_registry.install_crt_and_login(self, j2_ctx)
        #TODO(robnagler) thin pool creation one command, fixed size unless dev
        #TODO(robnagler) add live-restore?
        # live restore: https://docs.docker.com/engine/admin/live-restore
        # "live-restore": true,
        # live-restore does interrupt network due to proxies, --net=host
