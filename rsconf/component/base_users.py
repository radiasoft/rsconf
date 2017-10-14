# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

class T(component.T):
    def internal_build(self):
        self.buildt.require_component('base_os')
        self.append_root_bash(
            'rsconf_radia_run_as_user {} home'.format(self.hdb.rsconf_db_root_u))
        self.install_access(mode='400', owner=self.hdb.rsconf_db_root_u)
        # useradd -u 1000 -g vagrant -d /var/lib/vagrant vagrant

        # create vagrant with home /var/lib/vagrant for centos
        self.install_resource(
            'base_users/root_post_bivio_bashrc',
            {},
            '/root/.post_bivio_bashrc',
        )
        self.append_root_bash(
            'rsconf_radia_run_as_user {} home'.format(self.hdb.rsconf_db_run_u),
            'set +e +o pipefail',
            '. ~/.bashrc',
            'set -e -o pipefail',
        )
