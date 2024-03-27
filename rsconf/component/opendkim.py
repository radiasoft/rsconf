"""create dkim configuration for named and/or opendkim

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from pykern import pkio
from rsconf import component

_CONF_D = pkio.py_path("/etc/postfix")
_CONF_F = pkio.py_path("/etc/opendkim.conf")
_KEYS_D = _CONF_D.join("keys")
_SECRET_SUBDIR = "opendkim"


class T(component.T):
    def internal_build_compile(self):
        jc, z = self.j2_ctx_init()
        if self._named_compile(jc, z):
            return
        z.pksetdefault(port=8891)
        self.append_root_bash("rsconf_yum_install opendkim")
        z.update(
            external_ignore_list_f=_CONF_D.join("ExternalIgnoreList"),
            internal_hosts_f=_CONF_D.join("InternalHosts"),
            key_table_f=_CONF_D.join("KeyTable"),
            keys_d=_KEYS_D,
            run_u="opendkim",
            signing_table_f=_CONF_D.join("SigningTable"),
        )
        self._read_keys(jc, z)
        self.buildt.require_component("postfix").setup_opendkim(self)

    def internal_build_write(self):
        from rsconf.component import bop
        from rsconf import systemd

        jc = self.j2_ctx
        z = jc[self.name]
        if self._named_write(jc, z):
            return
        systemd.unit_prepare(self, jc, watch_files=(_CONF_D, _CONF_F))
        self.install_access(mode="400", owner=z.run_u)
        self._install_keys(jc, z)
        systemd.unit_enable(self, jc)
        access("400", run_u)

    def _read_keys(self, jc, z):
        from rsconf import db
        from rsconf.pkcli import opendkim

        def _find(secret_d):
            rv = PKDict()
            for d in z.domains:
                rv[d] = PKDict(rows=[], secret_d=secret_d.join(d))
                for p in pkio.sorted_glob(rv[d].secret_d.join("*.private")):
                    rv[d].rows.append(
                        PKDict(
                            private_f=p, txt_f=p.new(ext="txt"), selector=p.purebasename
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
            rv = ""
            for d in sorted(z._keys.keys()):
                rv += f"    '{d}' => [\n"
                for k in sorted(z._keys[d].rows, key=lambda x: x.dns.subdomain):
                    rv += f"        ['{k.dns.subdomain}' => '{k.dns.txt}'],\n"
                rv += "    ],\n"
            return rv

        if not z.named_conf_d:
            return False
        z.named_content = _content()
        self.install_resource2("opendkim-named.pl", z.named_conf_d)
        return z.named_only

    def _named_compile(self, jc, z):
        z.pksetdefault(named_conf_d=None)
        if not z.named_conf_d:
            return False
        z.pksetdefault(named_only=True)
        self._read_keys(jc, z)
        self.append_root_bash("rsconf_yum_install opendkim-tools")
        return z.named_only
