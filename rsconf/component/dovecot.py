# -*- coding: utf-8 -*-
u"""create dovecot configuration

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio
from pykern import pkjson
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from rsconf import systemd
from rsconf.component import base_users

CONF_ROOT_D = pkio.py_path('/etc/dovecot')
CONF_D = CONF_ROOT_D.join('conf.d')
_PASSWORD_SECRET_JSON_F = 'dovecot_password.json'
_PASSWORD_SECRET_F = 'dovecot_password'
_PASSWORD_VISIBILITY = 'host'


class T(component.T):

    def internal_build(self):
        # dependency not strictly necessary but logical
        self.buildt.require_component('postfix')
        self.append_root_bash('rsconf_yum_install dovecot')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.dovecot
        z.passdb_scheme = 'SHA512-CRYPT'
        z.user_mail_d = 'Maildir'
        # Needs to happen first to get read for install
        self.service_prepare([CONF_ROOT_D])
        z.pop_users_flattened = self._pop_users_flattened(j2_ctx, z)
        self._alias_users(j2_ctx, z)
        self.install_access(mode='400', owner=j2_ctx.rsconf_db.root_u)
        kc = self.install_tls_key_and_crt(j2_ctx.rsconf_db.host, CONF_ROOT_D)
        z.tls_crt = kc.crt
        z.tls_key = kc.key
        z.users_f = CONF_ROOT_D.join('users')
        z.run_u = 'dovecot'
        # general config needs public access
        self.install_access(mode='444')
        self.install_resource(
            'dovecot/rsconf.conf',
            j2_ctx,
            CONF_D.join('99-rsconf.conf'),
        )
        # password file needs to be readable by dovecot user
        self.install_access(
            mode='440',
            owner=j2_ctx.rsconf_db.root_u,
            group=z.run_u,
        )
        self.install_resource(
            'dovecot/users',
            j2_ctx,
            z.users_f,
        )

    def _setup_procmail(self, j2_ctx, z, i, is_alias=False):
        z.procmail_d = i.home_d.join('procmail')
        z.procmail_log_f = z.procmail_d.join('log')
        z.procmail_deliver = '! ' + i.email if is_alias \
            else '| /usr/libexec/dovecot/deliver'
        z.procmail_spam_level = i.setdefault('spam_level', 3)
        self.install_access(mode='700', owner=i.uid, group=i.gid)
        self.install_directory(i.home_d.join(z.user_mail_d))
        self.install_directory(z.procmail_d)
        self.install_access(mode='400')
        self.install_resource(
            'dovecot/procmailrc',
            j2_ctx,
            i.home_d.join('.procmailrc'),
        )
        self.install_access(mode='600')
        self.install_ensure_file_exists(z.procmail_log_f)

    def _pop_users_flattened(self, j2_ctx, z):
        pw_f = db.secret_path(
            j2_ctx,
            _PASSWORD_SECRET_JSON_F,
            visibility=_PASSWORD_VISIBILITY,
        )
        pw_modified = False
        if pw_f.check():
            with pw_f.open() as f:
                pw_db = pkjson.load_any(f)
        else:
            pw_db = pkcollections.Dict()
        res = []
        for u, pw in z.pop_users.items():
            if not u in pw_db:
                pw_modified = True
                pw_db[u] = '{' + z.passdb_scheme + '}' + _sha512_crypt(pw)
            i = base_users.hdb_info(j2_ctx, u)
            i.pw_hash = pw_db[u]
            i.home_d = db.user_home_path(j2_ctx, u)
            res.append(i)
            self._setup_procmail(j2_ctx, z, i)
        if pw_modified:
            pkjson.dump_pretty(pw_db, filename=pw_f)
        return sorted(res, key=lambda x: x.name)

    def _alias_users(self, j2_ctx, z):
        from rsconf.component import base_users

        for u in z.alias_users:
            i = base_users.hdb_info(j2_ctx, u)
            i.home_d = db.user_home_path(j2_ctx, u)
            self._setup_procmail(j2_ctx, z, i, is_alias=True)


def _sha512_crypt(password):
    from rsconf import db
    import crypt

    return crypt.crypt(password, '$6$' + db.random_string(length=16))
