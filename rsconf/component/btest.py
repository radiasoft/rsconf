# -*- coding: utf-8 -*-
u"""create btest runners

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import re
from pykern.pkdebug import pkdp
from rsconf import component
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf import db
        from rsconf.component import docker_registry
        from rsconf.component import bop

        self.buildt.require_component('docker', 'postgresql', 'postfix')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.btest
        z.run_u = j2_ctx.rsconf_db.run_u
        z.run_d = systemd.timer_prepare(self, j2_ctx)
        z.apps_d = z.run_d.join('apps')
        run_all = z.run_d.join('run_all')
        systemd.timer_enable(
            self,
            j2_ctx=j2_ctx,
            on_calendar=z.on_calendar,
            timer_exec=run_all,
            run_u=z.run_u,
        )
        z.source_code_d = bop.SOURCE_CODE_D
        self.install_access(mode='700', owner=z.run_u)
        self.install_directory(z.apps_d)
        for n in sorted(z.apps):
            a = j2_ctx[n]
            z.perl_root = a.perl_root
            self.install_access(mode='700')
            d = z.apps_d.join(n)
            self.install_directory(d)
            z.current_base = 'current'
            z.current_d = d.join(z.current_base)
            z.file_root = d.join('db')
            self.install_directory(z.file_root)
            z.backup_root = d.join('bkp')
            self.install_directory(z.backup_root)
            z.database = a.short_prefix + 'btest'
            z.log_d = d.join('log')
            # handles petshop
            z.root_for_unit = re.sub('::.*', '', z.perl_root)
            z.app_source_d = pkio.py_path('/usr/src/bop').join(z.root_for_unit)
            self.install_directory(z.log_d)
            # handles petshop
            z.root_for_acceptance = re.sub('::', '/', z.perl_root)
            z.perl_root_d = z.current_d.join(z.root_for_acceptance)
            z.facade_local_file_root = z.perl_root_d.join('files')
            z.http_home_page_uri = 'https://' + a.http_host
            z.http_host = a.http_host
            z.mail_host = a.mail_host
            z.email_user = z.run_u
            self.install_access(mode='400')
            z.bconf = pkcollections.Dict()
            for x in 'unit', 'acceptance':
                z.bconf_is_unit = x == 'unit'
                z.bconf[x] = d.join('bivio-{}.bconf'.format(x))
                self.install_resource(
                    'btest/bivio.bconf',
                    j2_ctx,
                    z.bconf[x],
                )
            self.install_access(mode='500')
            self.install_resource(
                'btest/run_one.sh',
                j2_ctx,
                d.join('run_one'),
            )
