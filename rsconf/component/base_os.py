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
_SSHD_CONF_F = pkio.py_path('/etc/ssh/sshd_config')

class T(component.T):

    def internal_build_compile(self):
        self.j2_ctx = self.hdb.j2_ctx_copy()
        jc = self.j2_ctx
        z = jc.base_os
        vgs = z.volume_groups
        cmds = ''
        for vgn in sorted(vgs.keys()):
            vg = vgs[vgn]
            for lv in self._sorted_logical_volumes(vg):
                cmds += "base_os_logical_volume '{}' '{}' '{}' '{}' '{}'\n".format(
                    lv.name, lv.gigabytes, vgn, lv.mount_d, lv.get('mode', 700),
                )
        z.logical_volume_cmds = cmds
        self.service_prepare([_JOURNAL_CONF_D], name='systemd-journald')
        self.service_prepare([_SSHD_CONF_F.dirpath()], name='sshd')

    def internal_build_write(self):
        jc = self.j2_ctx
        self._install_local_files(jc.rsconf_db.local_files)
        self.install_access(mode='700', owner=jc.rsconf_db.root_u)
        self.install_directory(_JOURNAL_CONF_D)
        self.install_access(mode='400')
        self.install_resource(
            'base_os/journald.conf',
            jc,
            _JOURNAL_CONF_D.join('99-rsconf.conf'),
        )
        self.install_resource(
            'base_os/60-rsconf-base.conf',
            jc,
            '/etc/sysctl.d/60-rsconf-base.conf',
        )
        self.install_resource(
            'base_os/sshd_config',
            jc,
            _SSHD_CONF_F,
        )
        self.install_access(mode='444')
        self.install_resource('base_os/hostname', jc, '/etc/hostname')
        self.install_resource('base_os/motd', jc, '/etc/motd')
        self.append_root_bash_with_main(jc)

    def _install_local_files(self, values):
        #TODO(robnagler) do we have to create directories and/or trigger on
        #  directory creation? For example, nginx rpm installs conf.d, which
        #  we will want to have local files for.
        for t in sorted(values.keys()):
            s = values[t]
            x = s.stat()
            self.install_access(
                mode='{:o}'.format(x.mode & 0o777),
                owner=x.owner,
                group=x.group,
            )
            # Local files overwrite existing (distro) files but if a component tries
            # to overwrite a local file, and error will occur.
            self.install_abspath(s, t, ignore_exists=True)

    def _sorted_logical_volumes(self, vg):
        res = []
        for k, v in vg.logical_volumes.items():
            if v.gigabytes == 0:
                continue
            v = pkcollections.Dict(v)
            v.name = k
            res.append(v)
        return iter(sorted(res, key=lambda x: x.mount_d))
