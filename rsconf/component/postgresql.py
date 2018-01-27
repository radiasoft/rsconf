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

class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        j2_ctx = self.hdb.j2_ctx_copy()
        j2_ctx.postgresql.run_d = j2_ctx.rsconf_db.host_run_d.join('postgresql')
        j2_ctx.postgresql.conf_d = j2_ctx.postgresql.run_d.join('data')
        j2_ctx.postgresql.conf_f = j2_ctx.postgresql.conf_d.join('postgresql.conf')
        self.install_access(mode='700', owner='postgres')
        self.append_root_bash('rsconf_yum_install postgresql-server')
        self.append_root_bash_with_resource(
            'postgresql/main.sh',
            j2_ctx,
            'postgresql_main',
        )
        systemd.unit_prepare(self, j2_ctx.postgresql.run_d)
        self.append_root_bash(
            'rsconf_append "{}" "{}" || true'.format(
                j2_ctx.postgresql.conf_f,
                "include 'rsconf.conf'",
            ),
        )
        self.install_access(mode='400', owner='postgres')
        kc = self.install_tls_key_and_crt(j2_ctx.rsconf_db.host, j2_ctx.postgresql.conf_d)
        j2_ctx.setdefault('postgresql', pkcollections.Dict()).update(
            ssl_cert_file=kc.crt.basename,
            ssl_key_file=kc.key.basename,
        )
        self.install_resource(
            'postgresql/rsconf.conf',
            j2_ctx,
            j2_ctx.postgresql.conf_d.join('rsconf.conf'),
        )
        self.install_resource(
            'postgresql/pg_hba.conf', j2_ctx, j2_ctx.postgresql.conf_d.join('pg_hba.conf'))
        systemd.unit_enable(self)
