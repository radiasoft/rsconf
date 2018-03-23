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
        from rsconf.component import logrotate

        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.postgresql
        z.run_d = j2_ctx.rsconf_db.host_run_d.join('postgresql')
        z.conf_d = z.run_d.join('data')
        z.conf_f = z.conf_d.join('postgresql.conf')
        z.run_u = 'postgres'
        z.log_filename = 'postgresql.log'
        z.log_d = pkio.py_path('/var/log/postgresql')
        # POSIT: pg_log is the default
        z.log_f = z.log_d.join(z.log_filename)
        self.install_access(mode='700', owner=z.run_u)
        self.append_root_bash('rsconf_yum_install postgresql-server')
        # Needs to be installed before main runs
        self.install_directory(z.log_d)
        self.append_root_bash_with_main(j2_ctx)
        systemd.unit_prepare(self, z.run_d)
        self.append_root_bash(
            'rsconf_append "{}" "{}" || true'.format(
                z.conf_f,
                "include 'rsconf.conf'",
            ),
        )
        self.install_access(mode='400', owner=z.run_u)
        kc = self.install_tls_key_and_crt(j2_ctx.rsconf_db.host, z.conf_d)
        j2_ctx.setdefault('postgresql', pkcollections.Dict()).update(
            ssl_cert_file=kc.crt.basename,
            ssl_key_file=kc.key.basename,
        )
        self.install_resource(
            'postgresql/rsconf.conf',
            j2_ctx,
            z.conf_d.join('rsconf.conf'),
        )
        self.install_resource(
            'postgresql/pg_hba.conf', j2_ctx, z.conf_d.join('pg_hba.conf'))
        self.install_access(mode='400', owner=j2_ctx.rsconf_db.root_u)
        logrotate.install_conf(self, j2_ctx)
        systemd.unit_enable(self)
