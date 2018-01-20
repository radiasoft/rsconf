# -*- coding: utf-8 -*-
u"""create postgresql configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio
from pykern.pkdebug import pkdp

_CONF_D = pkio.py_path('/var/lib/pgsql/data')

class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        j2_ctx = self.hdb.j2_ctx_copy()
        self.append_root_bash('rsconf_yum_install postgresql-server')
        self.append_root_bash_with_resource(
            'postgresql/initdb.sh',
            j2_ctx,
            'postgresql_initdb',
        )
        systemd.unit_prepare(self, _CONF_D)
        self.append_root_bash(
            'rsconf_append "{}" "{}" || true'.format(
                _CONF_D.join('postgresql.conf'),
                "include 'rsconf.conf'",
            ),
        )
        self.install_access(mode='400', owner='postgres')
        kc = self.install_tls_key_and_crt(j2_ctx.rsconf_db.host, _CONF_D)
        j2_ctx.setdefault('postgresql', pkcollections.Dict()).update(
            ssl_cert_file=kc.crt.basename,
            ssl_key_file=kc.key.basename,
        )
        self.install_resource(
            'postgresql/rsconf.conf',
            j2_ctx,
            _CONF_D.join('rsconf.conf'),
        )
        self.install_resource(
            'postgresql/pg_hba.conf', j2_ctx, _CONF_D.join('pg_hba.conf'))
        systemd.unit_enable(self)
