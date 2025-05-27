# -*- coding: utf-8 -*-
"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
import copy


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("base_os", "network")
        jc, z = self.j2_ctx_init()
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
        z.add_cmds = ""
        z._pre_bivio_bashrc = [(jc.rsconf_db.root_u,) * 2]
        for u in z.add:
            assert not u in z.added, "{}: duplicate user".format(u)
            i = copy.deepcopy(z.spec[u])
            i.name = u
            i.setdefault("gid", i.uid)
            s = 1 if i.setdefault("want_shell", False) else ""
            if s:
                z._pre_bivio_bashrc.append((i.name, i.gid))
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
            self._ssh_key(i)
            z.added[u] = i

    def internal_build_write(self):
        from rsconf.component import bkp

        def _pre_bivio_bashrc(jc):
            from rsconf import db

            for u, g in jc.base_users._pre_bivio_bashrc:
                self.install_access(mode="400", owner=u, group=g)
                self.install_resource(
                    "base_users/pre_bivio_bashrc",
                    jc,
                    db.user_home_path(u).join(".pre_bivio_bashrc"),
                )

        jc = self.j2_ctx
        self.install_access(mode="400", owner=jc.rsconf_db.root_u)
        self.install_resource(
            "base_users/root_post_bivio_bashrc",
            jc,
            "/root/.post_bivio_bashrc",
        )
        bkp.append_authorized_key(self, jc)
        self.append_root_bash_with_main(jc)
        # after main, because need users
        _pre_bivio_bashrc(jc)
        # latest bash environment used by other scripts
        self.append_root_bash("install_source_bashrc")

    def _ssh_key(self, user):
        if not self.buildt.get_component("network").j2_ctx.pkunchecked_nested_get(
            "network.public_ssh_ports"
        ) or not (k := user.get("public_ssh_key")):
            return
        self.append_root_bash(f"rsconf_append_authorized_key '{user.name}' '{k}'")

    def user_spec(self, name):
        return copy.deepcopy(self.j2_ctx.base_users.added[name])
