# -*- coding: utf-8 -*-
"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern.pkcollections import PKDict
import copy


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("base_os")
        jc = self.j2_ctx = self.hdb.j2_ctx_copy()
        z = jc.base_users
        z.add_cmds = ""
        z.email_aliases = PKDict()
        z.added = PKDict()
        z.setdefault("root_bashrc_aux", "")
        mailboxes = (
            set(
                jc.dovecot.alias_users + list(jc.dovecot.pop_users.keys()),
            )
            if "dovecot" in jc
            else set()
        )
        for u in z.add:
            assert not u in z.added, "{}: duplicate user".format(u)
            i = copy.deepcopy(z.spec[u])
            i.name = u
            i.setdefault("gid", i.uid)
            s = 1 if i.setdefault("want_shell", False) else ""
            z.add_cmds += "base_users_add '{name}' '{uid}' '{gid}' '{s}'\n".format(
                s=s, **i
            )
            z.email_aliases[u] = (
                None
                if i.setdefault(
                    "want_mailbox",
                    u in mailboxes,
                )
                else i.email
            )
            z.added[u] = i

    def internal_build_write(self):
        from rsconf.component import bkp

        jc = self.j2_ctx
        self.install_access(mode="400", owner=self.hdb.rsconf_db.root_u)
        self.install_resource(
            "base_users/root_post_bivio_bashrc",
            jc,
            "/root/.post_bivio_bashrc",
        )
        bkp.append_authorized_key(self, jc)
        self.append_root_bash_with_main(jc)

    def user_spec(self, name):
        return copy.deepcopy(self.j2_ctx.base_users.added[name])
