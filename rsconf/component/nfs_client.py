# -*- coding: utf-8 -*-
u"""create nfs client config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio
from pykern.pkdebug import pkdp
from rsconf import component


class T(component.T):

    def internal_build(self):
        self.buildt.require_component('base_all')

        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.nfs_client
        z.add_cmds = ''
        for server, mounts in z.mounts.items():
            for fs in mounts:
                z.add_cmds += "    nfs_client_add '{}:{}' '{}'\n".format(server, fs, fs)
        self.append_root_bash_with_main(j2_ctx)
