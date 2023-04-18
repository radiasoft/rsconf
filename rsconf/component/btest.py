# -*- coding: utf-8 -*-
"""create btest runners

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
        from rsconf.component import bop

        self.buildt.require_component("postgresql", "postfix")
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.btest
        z.run_u = j2_ctx.rsconf_db.run_u
        z.run_d = systemd.unit_run_d(j2_ctx, self.name)
        z.apps_d = z.run_d.join("apps")
        run_f = z.run_d.join("run")
        systemd.timer_prepare(
            self,
            j2_ctx,
            timer_exec=run_f
            on_calendar=z.on_calendar,
        )
        systemd.timer_enable(
            self,
            j2_ctx=j2_ctx,
            run_u=z.run_u,
        )
        z.source_code_d = bop.SOURCE_CODE_D
        z.app_run_u = j2_ctx.rsconf_db.run_u
        self.buildt.get_component("postfix").extend_local_host_names(
            [z.client_host],
        )
        self.install_access(mode="700", owner=z.app_run_u)
        self.install_directory(z.apps_d)
        z.home_d = db.user_home_path(j2_ctx, z.app_run_u)
        # POSIT: Bivio::Test::Language::HTTP
        z.mail_d = z.home_d.join("btest-mail")
        self.install_directory(z.mail_d)
        if j2_ctx.rsconf_db.channel == "dev":
            z.mail_copy_d = z.mail_d + "-copy"
            self.install_directory(z.mail_copy_d)
        self.install_access(mode="400")
        self.install_resource(
            "btest/vagrant_procmailrc",
            j2_ctx,
            z.home_d.join(".procmailrc"),
        )
        z.run_app_cmds = ""
        for n in sorted(z.apps):
            a = bop.merge_app_vars(j2_ctx, n)
            z.perl_root = a.perl_root
            self.install_access(mode="700", owner=z.app_run_u)
            z.app_run_d = z.apps_d.join(n)
            self.install_directory(z.app_run_d)
            z.service_name = "btest_" + n
            z.current_base = "current"
            z.current_d = z.app_run_d.join(z.current_base)
            z.file_root = z.app_run_d.join("db")
            self.install_directory(z.file_root)
            z.backup_root = z.app_run_d.join("bkp")
            self.install_directory(z.backup_root)
            z.database = a.short_prefix + "btest"
            z.log_d = z.app_run_d.join("log")
            # handles petshop
            z.root_for_unit = re.sub("::.*", "", z.perl_root)
            z.app_source_d = pkio.py_path("/usr/src/bop").join(z.root_for_unit)
            self.install_directory(z.log_d)
            # handles petshop
            z.root_for_acceptance = re.sub("::", "/", z.perl_root)
            z.perl_root_d = z.current_d.join(z.root_for_acceptance)
            z.facade_local_file_root = z.perl_root_d.join("files")
            z.http_home_page_uri = "https://" + a.http_host
            z.http_host = a.http_host
            z.mail_host = a.mail_host
            self.install_access(mode="400")
            z.bconf = pkcollections.Dict()
            for x in "unit", "acceptance":
                z.bconf_is_unit = x == "unit"
                z.bconf[x] = z.app_run_d.join("bivio-{}.bconf".format(x))
                self.install_resource(
                    "btest/bivio.bconf",
                    j2_ctx,
                    z.bconf[x],
                )
            self.install_access(mode="500")
            z.app_run_f = z.app_run_d.join("run")
            # TODO(robnagler) send mail
            self.install_resource(
                "btest/app_run.sh",
                j2_ctx,
                z.app_run_f,
            )
            z.run_app_cmds += "{}\n".format(z.app_run_f)
            bop.install_perl_rpms(
                self,
                j2_ctx,
                perl_root=z.perl_root,
            )
        self.install_access(mode="500", owner=z.run_u)
        self.install_resource(
            "btest/run.sh",
            j2_ctx,
            run_f,
        )
