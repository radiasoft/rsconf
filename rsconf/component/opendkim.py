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


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd
        from rsconf.component import network

        jc, z = self.j2_ctx_init()
        z.update(
            external_ignore_list_f=_CONF_D.join("ExternalIgnoreList"),
            internal_hosts_f=_CONF_D.join("InternalHosts"),
            key_table_f=_CONF_D.join("KeyTable"),
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
        systemd.unit_prepare(self, jc, watch_files=(_CONF_D, _CONF_F))
        self.rsconf_edit(
            _CONF_F,
            "^{}$".format(x),
            r"s<^#?\s*RPCNFSDCOUNT.*><{}>".format(x),
        )
        systemd.unit_enable(self, jc)
        access("400", run_u)
