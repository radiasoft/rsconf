# -*- coding: utf-8 -*-
u"""create postfix configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern.pkdebug import pkdp
from pykern import pkio
from rsconf import component
import re
import socket

# Fixing things and debugging
# Display queue: postqueue -p
# Delete all the deferred messages: postsuper -d ALL deferred
#


_CONF_D = pkio.py_path('/etc/postfix')

# We require three part host name
_HOSTNAME_RE = re.compile(r'^[^\.]+\.([^\.]+\.[^\.]+)$');

class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        self.buildt.require_component('postgrey', 'spamd')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.setdefault('postfix', pkcollections.Dict())
        self.append_root_bash('rsconf_yum_install postfix procmail')
        systemd.unit_prepare(self,j2_ctx, [_CONF_D])
        self._setup_virtual_aliases(j2_ctx, z)
        self._setup_sasl(j2_ctx, z)
        self._setup_mynames(j2_ctx, z)
        z.local_host_names_f = '/etc/postfix/local-host-names'
        # New install access
        self.install_access(mode='400', owner=j2_ctx.rsconf_db.root_u)
        kc = self.install_tls_key_and_crt(j2_ctx.rsconf_db.host, _CONF_D)
        self.install_access(mode='644')
        self.install_ensure_file_exists(z.local_host_names_f)
        z.update(
            tls_cert_file=kc.crt,
            tls_key_file=kc.key,
        )
        # see base_users.py which may clear email_aliases by setting to None
        z.aliases.update(j2_ctx.base_users.email_aliases)
        self.install_resource(
            'postfix/aliases',
            j2_ctx,
            '/etc/aliases',
        )
        self.append_root_bash_with_main(j2_ctx)
        systemd.unit_enable(self, j2_ctx)
        self.rsconf_service_restart_at_end()

    def _setup_mynames(self, j2_ctx, z):
        if 'myhostname' in z:
            h = z.myhostname
        elif 'primary_public_ip' in j2_ctx.network:
            h = socket.gethostbyaddr(j2_ctx.network.primary_public_ip)[0]
            assert _HOSTNAME_RE.search(h).group(1).lower() \
                == _HOSTNAME_RE.search(j2_ctx.rsconf_db.host).group(1).lower(), \
                '{}: reverse dns for {} does not match SLD of {}'.format(
                    h,
                    j2_ctx.network.primary_public_ip,
                    j2_ctx.rsconf_db.host,
                )
        else:
            h = j2_ctx.rsconf_db.host
        # just in case
        h = h.lower()
        # allow overrides, but also assert "h"
        z.setdefault('mydomain', _HOSTNAME_RE.search(h).group(1))
        z.setdefault('myorigin', h)
        z.setdefault('myhostname', h)

    def _setup_sasl(self, j2_ctx, z):
        if not z.setdefault('sasl_users', []):
            return
        self.install_access(mode='400', owner=j2_ctx.rsconf_db.root_u)
        z.sasl_users_flattened = []
        for domain, u in z.sasl_users.items():
            for user, password in u.items():
                z.sasl_users_flattened.append(
                    pkcollections.Dict(
                        domain=domain,
                        user=user,
                        password=password,
                    ),
                )
        self.install_resource(
            'postfix/smtpd-sasldb.conf',
            j2_ctx,
            '/etc/sasl2/smtpd-sasldb.conf',
        )
        assert j2_ctx.postfix.sasl_users_flattened
        self.hdb.postfix.sasl_users_flattened = j2_ctx.postfix.sasl_users_flattened

    def _setup_virtual_aliases(self, j2_ctx, z):
        if not z.setdefault('virtual_aliases', []):
            return
        self.install_access(mode='440', owner=j2_ctx.rsconf_db.root_u, group='mail')
        z.virtual_alias_f = _CONF_D.join('virtual_alias')
        z.virtual_alias_domains_f = _CONF_D.join('virtual_alias_domains')
        self.install_resource(
            'postfix/virtual_alias_domains', j2_ctx, z.virtual_alias_domains_f)
        self.install_resource(
            'postfix/virtual_alias', j2_ctx, z.virtual_alias_f)


def sasl_user_password(j2_ctx, user):
    # POSIT: user local part is globally unique
    for u in j2_ctx.postfix.sasl_users_flattened:
        if u.user == user:
            return u.password
    raise AssertionError('{}: not found in sasl users'.format(user))
