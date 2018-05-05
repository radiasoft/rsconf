# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
import copy

class T(component.T):
    def internal_build(self):
        from rsconf.component import bkp

        self.buildt.require_component('base_os')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.base_users
        self.install_access(mode='400', owner=self.hdb.rsconf_db.root_u)
        self.install_resource(
            'base_users/root_post_bivio_bashrc',
            j2_ctx,
            '/root/.post_bivio_bashrc',
        )
        bkp.append_authorized_key(self, j2_ctx)
        z.add_cmds = ''
        z.email_aliases = pkcollections.Dict()
        z.added = pkcollections.Dict()
        for u in z.add:
            assert not u in z.added, \
                '{}: duplicate user'.format(u)
            i = copy.deepcopy(z.spec[u])
            i.name = u
            i.setdefault('gid', i.uid)
            s = 1 if i.setdefault('want_shell', False) else ''
            z.add_cmds += "base_users_add '{name}' '{uid}' '{gid}' '{s}'\n".format(s=s, **i)
            z.email_aliases[u] = None if i.setdefault('want_mailbox', False) else i.email
            z.added[u] = i
        # POSIT: postfix will use this as an override for its aliases
        self.hdb.base_users.email_aliases = z.email_aliases
        self.hdb.base_users.added = z.added
        self.append_root_bash_with_main(j2_ctx)
