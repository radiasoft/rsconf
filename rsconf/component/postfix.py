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
import subprocess

# Fixing things and debugging
# Display queue: postqueue -p
# Delete all the deferred messages: postsuper -d ALL deferred
#


_CONF_D = pkio.py_path('/etc/postfix')

# We require three part host name
_HOSTNAME_RE = re.compile(r'^[^\.]+\.([^\.]+\.[^\.]+)$');

class T(component.T):

    def extend_local_host_names(self, names):
        self.j2_ctx.postfix.local_host_names.extend(names)

    def internal_build_compile(self):
        from rsconf import systemd

        self.buildt.require_component('network', 'postgrey', 'spamd')
        self.j2_ctx = self.hdb.j2_ctx_copy()
        jc = self.j2_ctx
        z = jc.setdefault('postfix', pkcollections.Dict())
        z.have_bop = False
        self.append_root_bash('rsconf_yum_install postfix procmail')
        systemd.unit_prepare(self, jc, [_CONF_D])
        self._setup_virtual_aliases(jc, z)
        self._setup_sasl(jc, z)
        self._setup_mynames(jc, z)
        self._setup_check_sender_access(jc, z)
        z.local_host_names = []

    def internal_build_write(self):
        from rsconf import systemd

        jc = self.j2_ctx
        z = jc.postfix
        z.mydestination = ','.join([z.myhostname, 'localhost'] + sorted(z.local_host_names))
        self.install_access(mode='400', owner=jc.rsconf_db.root_u)
        kc = self.install_tls_key_and_crt(jc.rsconf_db.host, _CONF_D)
        z.update(
            tls_cert_file=kc.crt,
            tls_key_file=kc.key,
        )
        self.install_access(mode='644')
        self.install_resource('postfix/main.cf', jc, _CONF_D.join('main.cf'))
        self.install_resource('postfix/master.cf', jc, _CONF_D.join('master.cf'))
        # see base_users.py which may clear email_aliases by setting to None
        z.aliases.update(jc.base_users.email_aliases)
        self.install_resource(
            'postfix/aliases',
            jc,
            '/etc/aliases',
        )
        self.append_root_bash_with_main(jc)
        systemd.unit_enable(self, jc)
        self.rsconf_service_restart_at_end()

    def setup_bop(self, mail_domains):
        self.j2_ctx.postfix.have_bop = True
        self.extend_local_host_names(mail_domains)

    def _setup_check_sender_access(self, jc, z):
        src = self.tmp_path()
        x = ['{} OK\n'.format(x) for x in sorted(z.get('whitelist_senders', []))]
        src.write(''.join(x))
        x =  _CONF_D.join('sender_access')
        z.check_sender_access_arg = 'texthash:' + str(x)
        self.install_access(mode='440', owner=jc.rsconf_db.root_u, group='mail')
        self.install_abspath(src, x)

    def _setup_mynames(self, jc, z):
        if 'myhostname' in z:
            h = z.myhostname
        elif 'primary_public_ip' in jc.network:
            h = socket.gethostbyaddr(jc.network.primary_public_ip)[0]
            assert _HOSTNAME_RE.search(h).group(1).lower() \
                == _HOSTNAME_RE.search(jc.rsconf_db.host).group(1).lower(), \
                '{}: reverse dns for {} does not match SLD of {}'.format(
                    h,
                    jc.network.primary_public_ip,
                    jc.rsconf_db.host,
                )
        else:
            h = jc.rsconf_db.host
        # just in case
        h = h.lower()
        # allow overrides, but also assert "h"
        z.setdefault('mydomain', _HOSTNAME_RE.search(h).group(1))
        z.setdefault('myorigin', h)
        z.setdefault('myhostname', h)
        if not z.get('mynetworks'):
            z.mynetworks = self.buildt.get_component('network').trusted_networks_as_str(',')

    def _setup_sasl(self, jc, z):
        z.have_sasl = bool(z.get('sasl_users'))
        if not z.have_sasl:
            return
        self.install_access(mode='400', owner=jc.rsconf_db.root_u)
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
            jc,
            '/etc/sasl2/smtpd-sasldb.conf',
        )
        assert jc.postfix.sasl_users_flattened
        self.hdb.postfix.sasl_users_flattened = jc.postfix.sasl_users_flattened

    def _setup_virtual_aliases(self, jc, z):
        z.have_virtual_aliases = bool(z.get('virtual_aliases'))
        if not z.have_virtual_aliases:
            return
        self.install_access(mode='440', owner=jc.rsconf_db.root_u, group='mail')
        z.virtual_alias_f = _CONF_D.join('virtual_alias')
        z.virtual_alias_maps = 'texthash:' + str(z.virtual_alias_f)
        z.virtual_alias_domains_f = _CONF_D.join('virtual_alias_domains')
        domains = sorted(z.virtual_aliases.keys())
        self.install_joined_lines(domains, z.virtual_alias_domains_f)
        a = []
        for d in domains:
            a.extend([
                '{}@{} {}'.format(x, d, z.virtual_aliases[d][x])
                    for x in sorted(z.virtual_aliases[d].keys())
            ])
        self.install_joined_lines(a, z.virtual_alias_f)
