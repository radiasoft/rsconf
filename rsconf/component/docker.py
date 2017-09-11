# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

_DAEMON_JSON = '/etc/docker/daemon.json'

class T(component.T):
    def internal_build(self):
        self.buildt.require_component('base_users')

        self.append_root_bash(
            "rsconf_service_prepare '{}' '{}'".format(
                self.name,
                _DAEMON_JSON,
            ),
        )
        v = pkcollections.Dict(volume_group='docker')
        self.install_access(mode='700', owner=self.hdb.root_u)
        self.install_directory('/etc/docker')
        self.install_access(mode='400', owner=self.hdb.root_u)
        self.install_resource(
            'docker/daemon.json',
            v,
            _DAEMON_JSON,
        )
        self.append_root_bash_with_resource(
            'docker/main.sh',
            v,
            'docker_main',
        )
        #TODO(robnagler) add live-restore?
        # live restore: https://docs.docker.com/engine/admin/live-restore
        # "live-restore": true,
