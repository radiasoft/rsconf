# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio
from pykern.pkdebug import pkdp
from rsconf import component

_JOURNAL_CONF_D = pkio.py_path('/etc/systemd/journald.conf.d')

class T(component.T):

    def internal_build(self):
        self.service_prepare([_JOURNAL_CONF_D], name='systemd-journald')
        self.install_access(mode='700', owner=self.hdb.rsconf_db.root_u)
        self.install_directory(_JOURNAL_CONF_D)
        j2_ctx = self.hdb.j2_ctx_copy()
        self.install_access(mode='400')
        self.install_resource(
            'base_os/journald.conf',
            j2_ctx,
            _JOURNAL_CONF_D.join('99-rsconf.conf'),
        )
        self.install_resource(
            'base_os/60-rsconf-base.conf',
            j2_ctx,
            '/etc/sysctl.d/60-rsconf-base.conf',
        )
        self.install_access(mode='444')
        self.install_resource('base_os/hostname', j2_ctx, '/etc/hostname')
        vgs = j2_ctx.base_os.volume_groups
        cmds = ''
        for vg in vgs:
            for lv in vg.logical_volumes:
                cmds += "base_os_logical_volume '{}' '{}' '{}' '{}'\n".format(
                    lv.name, lv.gigabytes, vg.name, lv.mount_d,
                )
        j2_ctx.base_os.logical_volume_cmds = cmds
        #TODO(robnagler) watch and update hostname? restart networking???
        self.append_root_bash_with_main(j2_ctx)
