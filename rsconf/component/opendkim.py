"""create postgrey configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from rsconf import component
from pykern import pkio

_CONF_D = pkio.py_path("/etc/postfix")
_CONF_F = pkio.py_path("/etc/opendkim.conf")
_KEYS_D = _CONF_D.join("keys")
_SECRET_SUBDIR = "opendkim"


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd
        from rsconf.component import network

        jc, z = self.j2_ctx_init()
        if z.get("named_only"):
            self._named_compile(jc, z)
            return
        self.append_root_bash("rsconf_yum_install opendkim")
        z.update(
            external_ignore_list_f=_CONF_D.join("ExternalIgnoreList"),
            internal_hosts_f=_CONF_D.join("InternalHosts"),
            key_table_f=_CONF_D.join("KeyTable"),
            keys_d=_KEYS_D,
            keys=PKDict(),
            port=8891,
            run_u="opendkim",
            signing_table_f=_CONF_D.join("SigningTable"),
        )
        self.buildt.require_component("postfix").setup_opendkim(self)

    def internal_build_write(self):
        from rsconf.component import bop
        from rsconf import systemd

        jc = self.j2_ctx
        z = jc[self.name]
        if z.get("named_only"):
            self._named_write(jc, z)
            return
        systemd.unit_prepare(self, jc, watch_files=(_CONF_D, _CONF_F))
        self.install_access(mode="400", owner=z.run_u)
        self._install_keys(z.domains)
        systemd.unit_enable(self, jc)
        access("400", run_u)

    def _gen_keys(self, domains, named=False):
        def _find(secret_d):
            rv = PKDict()
            for d in domains:
                rv[d] = PKDict(keys=[], secret_d=secret_d.join(d))
                for p in pkio.sorted_glob(rv[d].secret_d.join("*.private")):
                    rv[d].append(
                        PKDict(
                            private_f=p, txt_f=p.new(ext="txt"), selector=p.purebasename
                        )
                    )
            return rv

        rv = _find(db.secret_path(j2_ctx, SECRET_SUBDIR, visibility="global"))
        for d, v in rv.items():
            if not v.keys:
                if named:
                    v.keys.append(rsconf.pkcli.opendkim.gen_key(v.secret_d, d))
                else:
                    raise AssertionError(f"missing keys for domain={d}")
            for k in v.keys:
                k.dns = rsconf.pkcli.opendkim.parse_txt(k.txt_f)
        return rv

    def _named_write(self, jc, z):
        pass

    def _named_compile(self, jc, z):
        jc = self.j2_ctx
        z = jc[self.name]

        self.append_root_bash("rsconf_yum_install opendkim")
        # NamedConf.zones.domain.txt = [[key, txt]]
