# -*- coding: utf-8 -*-
"""create postfix configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from pykern import pkio
from pykern import pkjson
from rsconf import component
import re
import socket

# Fixing things and debugging
# Display queue: postqueue -p
# Delete all the deferred messages: postsuper -d ALL deferred
#

_CONF_D = pkio.py_path("/etc/postfix")

# We require three part host name
_HOSTNAME_RE = re.compile(r"^[^\.]+\.([^\.]+\.[^\.]+)$")

_SASL_PASSWORD_JSON_F = "postfix_host_sasl_password.json"

_SASL_PASSWORD_PREFIX = "postfix@"


class T(component.T):
    def extend_local_host_names(self, names):
        self.j2_ctx.postfix.local_host_names.extend(names)

    def internal_build_compile(self):
        from rsconf import systemd

        self.buildt.require_component("network", "base_users")
        self.j2_ctx = self.hdb.j2_ctx_copy()
        jc = self.j2_ctx
        z = jc.setdefault("postfix", PKDict())
        z.base_users = self.buildt.get_component("base_users")
        nc = self.buildt.get_component("network")
        z.have_public_smtp = not z.get("smart_host")
        if z.have_public_smtp:
            nc.add_public_tcp_ports(["smtp", "submission"])
            self.buildt.require_component("postgrey", "spamd")
        else:
            nc.add_trusted_tcp_ports(["smtp", "submission"])
        z.have_bop = False
        self.append_root_bash(
            "rsconf_yum_install postfix procmail cyrus-sasl cyrus-sasl-plain"
        )
        systemd.unit_prepare(self, jc, [_CONF_D])
        z.have_virtual_aliases = bool(z.get("virtual_aliases"))
        z.pksetdefault(
            sasl_users=PKDict,
            sasl_host_users=[],
        )
        z.have_sasl = bool(z.get("sasl_users") or z.get("sasl_host_users"))
        z.local_host_names = []
        self._setup_mynames(jc, z)

    def internal_build_write(self):
        from rsconf import systemd

        jc = self.j2_ctx
        z = jc.postfix
        assert (
            bool(z.have_sasl or z.local_host_names or z.have_virtual_aliases)
            == z.have_public_smtp
        ), "either sasl_users, sasl_host_users, btest, or bop, or need a smarthost"
        z.mydestination = ",".join(
            [z.myhostname, "localhost"] + sorted(z.local_host_names),
        )
        self._write_check_sender_access(jc, z)
        self._write_sasl_password(jc, z)
        self._write_sasl(jc, z)
        self._write_virtual_aliases(jc, z)
        self.install_access(mode="400", owner=jc.rsconf_db.root_u)
        kc = self.install_tls_key_and_crt(jc.rsconf_db.host, _CONF_D)
        z.update(
            tls_cert_file=kc.crt,
            tls_key_file=kc.key,
        )
        self.install_access(mode="644")
        for f in "main.cf", "master.cf":
            self.install_resource("postfix/" + f, jc, _CONF_D.join(f))
        # see base_users.py which may clear email_aliases
        # by setting a value in this list to None
        z.aliases.update(z.base_users.j2_ctx.base_users.email_aliases)
        self.install_resource(
            "postfix/aliases",
            jc,
            "/etc/aliases",
        )
        self.append_root_bash_with_main(jc)
        systemd.unit_enable(self, jc)
        self.rsconf_service_restart_at_end()

    def setup_bop(self, mail_domains):
        z = self.j2_ctx.postfix
        z.have_bop = True
        assert (
            z.have_public_smtp
        ), "if bop is installed, must have_public_smtp (smart_host must not be set)"
        self.extend_local_host_names(mail_domains)

    def _setup_mynames(self, jc, z):
        jc = self.j2_ctx
        nc = self.buildt.get_component("network")
        # allow overrides, but also assert "h"
        h = z.get("myhostname")
        rh = jc.rsconf_db.host.lower()
        if not h:
            ip = nc.unchecked_public_ip()
            h = socket.gethostbyaddr(ip)[0] if ip else rh
        h = h.lower()
        assert _HOSTNAME_RE.search(h).group(1) == _HOSTNAME_RE.search(rh).group(
            1
        ), "primary does not match SLD of {}".format(h, rh)
        z.setdefault("mydomain", _HOSTNAME_RE.search(h).group(1))
        z.setdefault("myorigin", h)
        z.setdefault("myhostname", h)
        if not z.get("mynetworks"):
            z.mynetworks = ",".join(nc.trusted_nets())

    def _write_check_sender_access(self, jc, z):
        src = self.tmp_path()
        x = ["{} OK\n".format(x) for x in sorted(z.get("whitelist_senders", []))]
        src.write("".join(x))
        x = _CONF_D.join("sender_access")
        z.check_sender_access_arg = "texthash:" + str(x)
        self.install_access(mode="440", owner=jc.rsconf_db.root_u, group="mail")
        self.install_abspath(src, x)

    def _write_sasl(self, jc, z):
        if not z.have_sasl:
            return

        def _host_users():
            res = []
            j = _sasl_password_path(jc)
            if not j.check():
                return res
            with j.open() as f:
                y = pkjson.load_any(f)
            for h in z.sasl_host_users:
                u = _SASL_PASSWORD_PREFIX + h
                x = u.split("@")
                res.append(
                    PKDict(
                        domain=x[1],
                        user=x[0],
                        password=y[u],
                    ),
                )
            return res

        def _users():
            res = []
            for domain, u in z.sasl_users.items():
                for user, password in u.items():
                    res.append(
                        PKDict(
                            domain=domain,
                            user=user,
                            password=password,
                        ),
                    )
            return res

        self.install_access(mode="400", owner=jc.rsconf_db.root_u)
        r = _users() + _host_users()
        z.sasl_users_flattened = sorted(r, key=lambda x: x.user + x.domain)
        self.install_resource(
            "postfix/smtpd-sasldb.conf",
            jc,
            "/etc/sasl2/smtpd-sasldb.conf",
        )

    def _write_sasl_password(self, jc, z):
        if z.have_public_smtp:
            return
        z.relayhost = "[{}]:submission".format(z.get("smart_host").lower())
        u, p = host_init(jc, jc.rsconf_db.host)
        fn = _CONF_D.join("sasl_password")
        l = "{} {}:{}".format(z.relayhost, u, p)
        self.install_joined_lines([l], fn)
        z.sasl_password_maps = "texthash:" + str(fn)

    def _write_virtual_aliases(self, jc, z):
        if not z.have_virtual_aliases:
            return
        self.install_access(mode="440", owner=jc.rsconf_db.root_u, group="mail")
        z.virtual_alias_f = _CONF_D.join("virtual_alias")
        z.virtual_alias_maps = "texthash:" + str(z.virtual_alias_f)
        z.virtual_alias_domains_f = _CONF_D.join("virtual_alias_domains")
        domains = sorted(z.virtual_aliases.keys())
        self.install_joined_lines(domains, z.virtual_alias_domains_f)
        a = []
        for d in domains:
            a.extend(
                [
                    "{}@{} {}".format(x, d, z.virtual_aliases[d][x])
                    for x in sorted(z.virtual_aliases[d].keys())
                ]
            )
        self.install_joined_lines(a, z.virtual_alias_f)


def host_init(j2_ctx, host):
    from rsconf import db

    jf = _sasl_password_path(j2_ctx)
    if jf.check():
        with jf.open() as f:
            y = pkjson.load_any(f)
    else:
        y = PKDict()
    u = _SASL_PASSWORD_PREFIX + host
    if not u in y:
        y[u] = db.random_string()
        pkjson.dump_pretty(y, filename=jf)
    return u, y[u]


def _sasl_password_path(j2_ctx):
    from rsconf import db

    return db.secret_path(
        j2_ctx, _SASL_PASSWORD_JSON_F, visibility=db.VISIBILITY_GLOBAL
    )
