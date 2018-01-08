# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern.pkdebug import pkdp
from rsconf import component

class T(component.T):

    def internal_build(self):
        self.install_access(mode='400', owner=self.hdb.rsconf_db_root_u)
        j2_ctx = pkcollections.Dict(self.hdb)
        self.install_resource(
            'base_os/60-rsconf-base.conf',
            j2_ctx,
            '/etc/sysctl.d/60-rsconf-base.conf',
        )
        self.install_access(mode='444', owner=self.hdb.rsconf_db_root_u)
        self.install_resource('base_os/hostname', j2_ctx, '/etc/hostname')
        vgs = j2_ctx.base_os_volume_groups
        cmds = ''
        for vg in vgs:
            for lv in vg.logical_volumes:
                cmds += "base_os_logical_volume '{}' '{}' '{}' '{}'\n".format(
                    lv.name, lv.gigabytes, vg.name, lv.mount_d,
                )
        j2_ctx.base_os_logical_volume_cmds = cmds
        #TODO(robnagler) watch and update hostname? restart networking???
        self.append_root_bash_with_resource(
            'base_os/main.sh',
            j2_ctx,
            'base_os_main',
        )
