# -*- coding: utf-8 -*-
u"""create postfix configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkio
from rsconf import component

_CONF_D = pkio.py_path('/etc/postfix')

class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        self.buildt.require_component('postgrey', 'spamd')
        j2_ctx = pkcollections.Dict(self.hdb)
        self.append_root_bash('rsconf_yum_install postfix')
        systemd.unit_prepare(self, _CONF_D)
        self.install_access(mode='400', owner=j2_ctx.rsconf_db_root_u)
        kc = self.install_tls_key_and_crt(j2_ctx.rsconf_db_host, _CONF_D)
        j2_ctx.postgresql_ssl_cert_file = kc.crt
        j2_ctx.postgresql_ssl_key_file = kc.key
        self.append_root_bash_with_resource(
            'postfix/main.sh',
            j2_ctx,
            'postfix_main',
        )
        systemd.unit_enable(self)
