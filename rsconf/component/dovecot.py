# -*- coding: utf-8 -*-
u"""create dovecot configuration

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio
from pykern.pkdebug import pkdp

CONF_ROOT_D = pkio.py_path('/etc/dovecot')
CONF_D = CONF_ROOT_D.join('conf.d')
_PASSWORD_SECRET_JSON_F = 'dovecot_password.json'
_PASSWORD_SECRET_F = 'dovecot_password'
_PASSWORD_VISIBILITY = 'host'

class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        # dependency not strictly necessary but logical
        self.buildt.require_component('postfix')
        self.append_root_bash('rsconf_yum_install dovecot')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.dovecot
        z.passdb_scheme = 'SHA512-CRYPT'
        z.user_mail_d = '~/Maildir'
        # Needs to happen first to get read for install
        self.service_prepare([CONF_D])
        self.install_access(mode='400', owner=j2_ctx.rsconf_db.root_u)
        kc = self.install_tls_key_and_crt(j2_ctx.rsconf_db.host, CONF_D)
        z.tls_crt = kc.crt
        z.tls_key = kc.key
        z.users_f = CONF_ROOT_D.join('users')
        z.users_flattened = self._users_flattened(j2_ctx, z)
        self.install_access(mode='400')
        self.install_resource(
            'dovecot/rsconf.conf',
            j2_ctx,
            CONF_D.join('99-rsconf.conf'),
        )
        # passwords in a separate file, perhaps in a user file?
        self.install_access(
            mode='440',
            owner=j2_ctx.rsconf_db.root_u,
            group='dovecot',
        )
        self.install_resource(
            'dovecot/users',
            j2_ctx,
            z.users_f,
        )
        self.append_root_bash_with_main(j2_ctx)


    def _users_flattened(self, j2_ctx, z):
        from pykern import pkjson
        from rsconf import db
        from rsconf.component import base_users
        import subprocess

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
                pw_db[u] = subprocess.check_output(
                    ['dovecot', 'pw', '-s', z.passdb_scheme, '-p', pw],
                ).strip()
            i = base_users.hdb_info(j2_ctx, u)
            i.pw_hash = pw_db[u]
            i.home_d = db.user_home_path(j2_ctx, u)
            res.append(i)
        if pw_modified:
            pkjson.dump_pretty(pw_db, filename=pw_f)
        return sorted(res, key=lambda x: x.name)
