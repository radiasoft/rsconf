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
        j2_ctx = self.hdb.j2_ctx_copy()
        self.install_access(mode='400', owner=self.hdb.rsconf_db.root_u)
        self.install_resource(
            'base_users/root_post_bivio_bashrc',
            j2_ctx,
            '/root/.post_bivio_bashrc',
        )
        self.append_root_bash_with_main(j2_ctx)
