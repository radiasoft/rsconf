"""create dkim configuration for named and/or opendkim

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from pykern import pkio
from pykern import pkjson
from rsconf import component

_CONF_D = pkio.py_path("/etc/opendkim")
_CONF_F = _CONF_D.new(ext=".conf")
_SECRET_SUBDIR = "opendkim"


class T(component.T):
    def internal_build_compile(self):
        jc, z = self.j2_ctx_init()
        if self._named_compile(jc, z):
            return
        self.buildt.require_component("postfix")
        self.append_root_bash("rsconf_yum_install opendkim")
        z.pksetdefault(port=8891, smtp_clients=[])
        z.update(
            external_ignore_list_f=_CONF_D.join("ExternalIgnoreList"),
            internal_hosts_f=_CONF_D.join("InternalHosts"),
            key_table_f=_CONF_D.join("KeyTable"),
            keys_d=_CONF_D.join("keys"),
            run_u="opendkim",
            signing_table_f=_CONF_D.join("SigningTable"),
        )
        self._read_keys(jc, z)
        self.buildt.get_component("postfix").setup_opendkim(self)
        self._trusted_hosts(jc, z)

    def internal_build_write(self):
        from rsconf.component import bop
        from rsconf import systemd

        jc = self.j2_ctx
        z = jc[self.name]
        if self._named_write(jc, z):
            return
        systemd.unit_prepare(self, jc, watch_files=(_CONF_D, _CONF_F))
        self._install_conf(jc, z, self._install_keys(jc, z))
        systemd.unit_enable(self, jc)

    def _install_conf(self, jc, z, key_list):
        def _key_table():
            for k in key_list:
                yield f"{k.fq_selector} {k.domain}:{k.selector}:{k.path}"

        def _signing_table():
            for k in key_list:
                yield f"*@{k.domain} {k.fq_selector}"

        self.install_resource2("opendkim.conf", _CONF_D.dirpath())
        self.install_joined_lines(_key_table(), z.key_table_f)
        self.install_joined_lines(_signing_table(), z.signing_table_f)
        # The docs are not 100% clear about the difference between external
        # and internal, but it seems like this is the best approach for now.
        self.install_joined_lines(z._trusted_hosts, z.internal_hosts_f)
        self.install_joined_lines(z._trusted_hosts, z.external_ignore_list_f)

    def _install_keys(self, jc, z):
        def _dirs():
            rv = []
            for d, v in self._iter_keys(z):
                self.install_access(mode="700", owner=z.run_u)
                p = z.keys_d.join(d)
                self.install_directory(p)
                rv.append((v, p))
            return rv

        rv = []
        for v, p in _dirs():
            self.install_access(mode="400")
            for k in self._iter_key_rows(v):
                rv.append(
                    PKDict(
                        domain=v.domain,
                        fq_selector=f"{k.selector}._domainkey.{v.domain}",
                        path=self.install_abspath(
                            k.private_f,
                            p.join(k.private_f.basename),
                        ),
                        selector=k.selector,
                    ),
                )
        return rv

    def _iter_keys(self, z):
        for d in sorted(z._keys.keys()):
            yield d, z._keys[d]

    def _iter_key_rows(self, key):
        for k in sorted(key.rows, key=lambda x: x.dns.subdomain):
            yield k

    def _read_keys(self, jc, z):
        from rsconf import db
        from rsconf.pkcli import opendkim

        def _find(secret_d):
            rv = PKDict()
            for d in z.domains:
                rv[d] = PKDict(domain=d, rows=[], secret_d=secret_d.join(d))
                for p in pkio.sorted_glob(rv[d].secret_d.join("*.private")):
                    rv[d].rows.append(
                        PKDict(
                            private_f=p,
                            txt_f=p.new(ext="txt"),
                            selector=p.purebasename,
                        )
                    )
            return rv

        z._keys = _find(db.secret_path(jc, _SECRET_SUBDIR, visibility="global"))
        for d, v in z._keys.items():
            if not v.rows:
                if not z.named_conf_d:
                    raise AssertionError(f"missing keys for domain={d}")
                v.rows.append(opendkim.gen_key(v.secret_d, d))
            for k in v.rows:
                k.dns = opendkim.parse_txt(k.txt_f)

    def _named_write(self, jc, z):
        def _content():
            return PKDict(
                {d: _content_rows(s) for d, s in _normalize_domains().items()}
            )

        def _content_rows(subdomains):
            rv = PKDict()
            for s in subdomains:
                for r in self._iter_key_rows(s.rows):
                    rv[f"{r.dns.subdomain}{s.prefix}"] = r.dns.txt
            return rv

        def _normalize_domains():
            rv = PKDict()
            for d, v in self._iter_keys(z):
                x = _split_domain(d)
                rv.setdefault(x.sld, []).append(x.pkupdate(rows=v))
            return rv

        def _split_domain(full_name):
            x = full_name.split(".")
            return PKDict(
                sld=".".join(x[-2:]),
                prefix=".".join([""] + x[0:-2]) if len(x) > 2 else "",
            )

        if not z.named_conf_d:
            return False
        self.install_access(mode="400", owner=jc.rsconf_db.root_u)
        self.install_json(_content(), z.named_conf_d.join("opendkim-named.json"))
        return z.named_only

    def _named_compile(self, jc, z):
        z.pksetdefault(named_conf_d=None)
        if not z.named_conf_d:
            return False
        z.pksetdefault(named_only=True)
        self._read_keys(jc, z)
        return z.named_only

    def _trusted_hosts(self, jc, z):
        from rsconf import db
        import socket

        def _ip(name_or_ip):
            if any(c.isalpha() for c in name_or_ip):
                return socket.gethostbyname(name_or_ip)
            return name_or_ip

        def _iter():
            n = self.buildt.get_component("network")
            for h in [
                n.ip_for_this_host(),
                n.unchecked_public_ip(),
            ] + z.smtp_clients:
                if h is not None and (h := _ip(h)):
                    if h != db.LOCAL_IP:
                        yield h

        z._trusted_hosts = ["localhost", db.LOCAL_IP] + sorted(set(_iter()))
