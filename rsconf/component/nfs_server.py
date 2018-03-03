# -*- coding: utf-8 -*-
u"""create nfs server config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio
from pykern.pkdebug import pkdp
from rsconf import component

_EXPORTS_D = pkio.py_path('/etc/exports.d')
_SYSCONFIG_NFS = pkio.py_path('/etc/sysconfig/nfs')
_OPTIONS = 'rw,no_root_squash,no_subtree_check,async,secure'

class T(component.T):

    def internal_build(self):
        self.buildt.require_component('base_all')

        # Must be first to ensure /etc/exports.d exists
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.nfs_server
        self.append_root_bash('rsconf_yum_install nfs-utils')
        # Don't use "nfs", because "systemctl is-active nfs" returns unknown, b/c
        # nfs is a symlink to nfs-server.
        self.service_prepare((_EXPORTS_D, _SYSCONFIG_NFS), name='nfs-server')
        self.install_access(mode='400', owner=self.hdb.rsconf_db.root_u)
        for fs, clients in z.exports.items():
            z.client_args = ' '.join(['{}({})'.format(c, _OPTIONS) for c in clients])
            z.fs = fs
            # /foo/bar => foo_bar.exports
            f = fs[1:].replace('/', '_') + '.exports'
            self.install_resource('nfs_server/exports', j2_ctx, _EXPORTS_D.join(f))
        x = 'RPCNFSDCOUNT={}'.format(z.num_servers)
        self.rsconf_edit(
            _SYSCONFIG_NFS,
            '^{}$'.format(x),
            's<^#\s*RPCNFSDCOUNT.*><{}>'.format(x),
        )
