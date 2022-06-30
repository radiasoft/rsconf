# -*- coding: utf-8 -*-
"""create bop apps for a host

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import re
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from rsconf import systemd
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio


SOURCE_CODE_D = "/usr/share/Bivio-bOP-src"

PETSHOP_ROOT = "Bivio::PetShop"

COMMON_RPMS = ("bivio-perl", "perl-Bivio")

_DEFAULT_CLIENT_MAX_BODY_SIZE = "50M"


class T(component.T):
    def internal_build(self):
        from rsconf.component import db_bkp
        from rsconf.component import logrotate
        from rsconf.component import nginx

        if self.name == "bop":
            self.hdb.bop.update(
                pkcollections.Dict(
                    aux_directives="",
                    facade_setup_cmds="",
                    mail_domains=pkcollections.Dict(),
                )
            )
            self.buildt.require_component("postgresql", "nginx", "postfix", "db_bkp")
            for n in sorted(self.hdb.bop.apps):
                appt = T(n, self.buildt)
                appt.bopt = self
                self.buildt.build_component(appt)
            j2_ctx = self.hdb.j2_ctx_copy()
            z = j2_ctx.bop
            z.mail_domain_keys = sorted(z.mail_domains.keys())
            self.buildt.get_component("postfix").setup_bop(z.mail_domain_keys)
            z.setdefault("client_max_body_size", _DEFAULT_CLIENT_MAX_BODY_SIZE)
            nginx.update_j2_ctx_and_install_access(self, j2_ctx)
            self.install_resource(
                "bop/nginx_common.conf",
                j2_ctx,
                nginx.CONF_D.join("bop_common.conf"),
            )
            # after the rpms are installed
            self.append_root_bash_with_main(j2_ctx)
            return
        j2_ctx = self.hdb.j2_ctx_copy()
        z = merge_app_vars(j2_ctx, self.name)
        watch = install_perl_rpms(self, j2_ctx, perl_root=z.perl_root)
        systemd.custom_unit_prepare(self, j2_ctx, watch)
        systemd.custom_unit_enable(
            self,
            j2_ctx,
            reload="reload",
            stop="stop",
            resource_d="bop",
            run_u=z.run_u,
            run_d_mode="711",
        )
        self.install_access(mode="700", owner=z.run_u)
        # bkp is only used by Societas/Biz/Util/Club.pm
        for d in "bkp", "db", "log", "logbop":
            x = z.run_d.join(d)
            z["{}_d".format(d)] = x
            self.install_directory(x)
        self.install_access(mode="711")
        z.srv_d = z.run_d.join("srv")
        self.install_directory(z.srv_d)
        self.install_access(mode="440")
        self.install_resource("bop/httpd.conf", j2_ctx, z.conf_f)
        self.install_resource("bop/bivio.bconf", j2_ctx, z.bconf_f)
        self.install_resource("bop/initdb.sh", j2_ctx, z.initdb_f)
        self.install_symlink(
            pkio.py_path("/etc/httpd/modules"),
            z.run_d.join("modules"),
        )
        logrotate.install_conf(self, j2_ctx, resource_d="bop")
        # Init db after the unit files are installed
        self.append_root_bash(z.initdb_cmd)
        self.bopt.hdb.bop.aux_directives += j2_ctx.get("bop.nginx_aux_directives", "")
        self._install_vhosts(j2_ctx)
        db_bkp.install_script_and_subdir(
            self,
            j2_ctx,
            resource_d="bop",
            run_u=z.run_u,
            run_d=z.run_d,
        )

    def _install_facade_static_files_d(self, j2_ctx, z, vh):
        z.facade_static_files_d = z.srv_d.join(vh.facade)
        self.install_access(mode="711", owner=z.run_u)
        self.install_directory(z.facade_static_files_d)
        m_d = z.facade_static_files_d.join("m")
        z.maintenance_uri = "/m/maintenance.html"
        # most neutral format, because we have jpg, gif, and png
        z.logo_uri = "/m/logo.png"
        self.install_directory(m_d)
        self.install_access(mode="444")
        self.install_resource(
            "bop/maintenance.html",
            j2_ctx,
            m_d.join("maintenance.html"),
        )
        self.bopt.hdb.bop.facade_setup_cmds += (
            "bop_facade_setup '{}' '{}' '{}'\n".format(
                z.local_file_root_d.join(vh.facade, "plain"),
                z.facade_static_files_d,
                z.logo_uri,
            )
        )

    def _install_vhosts(self, j2_ctx):
        from rsconf.component import nginx

        z = j2_ctx.bop
        for vh in z.vhosts:
            h, aliases = _domain(j2_ctx, vh)
            self._install_facade_static_files_d(j2_ctx, z, vh)
            z.aux_directives = vh.get("nginx_aux_directives", "")
            z.redirects = nginx.render_redirects(self, j2_ctx, aliases, h)
            nginx.install_vhost(
                self,
                vhost=h,
                backend_host=j2_ctx.rsconf_db.host,
                backend_port=z.listen_base + 1,
                resource_d="bop",
                j2_ctx=j2_ctx,
            )
            if "receive_mail" in vh:
                assert (
                    not "mail_domains" in vh
                ), "{}: receive_mail and mail_domains: both set".format(h)
                if vh.receive_mail:
                    vh.mail_domains = [h]
            for m in vh.get("mail_domains", []):
                self.bopt.hdb.bop.mail_domains[m] = z.listen_base


def install_perl_rpms(compt, j2_ctx, perl_root=None):
    from rsconf import systemd

    if not compt.hdb.bop.setdefault("_perl_installed", False):
        compt.hdb.bop._perl_installed = True
        compt.append_root_bash("install_repo_eval biviosoftware/container-perl base")
    todo = list(COMMON_RPMS)
    if perl_root and perl_root != PETSHOP_ROOT:
        todo.append("perl-{}".format(perl_root))
    watch = []
    c = j2_ctx.bop.setdefault("perl_rpm_channel", j2_ctx.rsconf_db.channel)
    for r in todo:
        watch.append(compt.install_perl_rpm(j2_ctx, r, channel=c))
    return watch


def merge_app_vars(j2_ctx, app_name):
    z = j2_ctx.bop
    z.setdefault("is_production", j2_ctx.rsconf_db.channel == "prod")
    z.is_test = not z.is_production
    z.run_u = j2_ctx.rsconf_db.run_u
    db.merge_dict(z, j2_ctx[app_name])
    z.app_name = app_name
    # all apps are secured by TLS now
    z.can_secure = True
    z.setdefault("bconf_aux", "")
    z.setdefault("block_goto", False)
    z.setdefault("client_max_body_size", _DEFAULT_CLIENT_MAX_BODY_SIZE)
    z.source_code_d = SOURCE_CODE_D
    # Assumed by PetShop's crm-ticket-deletion.btest
    z.want_status_email = z.perl_root == PETSHOP_ROOT
    if z.is_test:
        z.http_host = _domain(j2_ctx, z.vhosts[0])[0]
        z.mail_host = z.http_host
    z.run_d = systemd.unit_run_d(j2_ctx, app_name)
    z.conf_f = z.run_d.join("httpd.conf")
    z.bconf_f = z.run_d.join("bivio.bconf")
    z.initdb_f = z.run_d.join("initdb.sh")
    z.initdb_cmd = "source {}".format(z.initdb_f)
    z.log_postrotate_f = z.run_d.join("reload")
    z.httpd_cmd = "/usr/sbin/httpd -d '{}' -f '{}'".format(z.run_d, z.conf_f)
    z.local_file_root_d = pkio.py_path("/var/www/facades")
    return z


def _domain(j2_ctx, vh):
    res = vh.get("domains")
    if res:
        return res[0], res[1:]
    return vh.get("facade") + "." + j2_ctx.bop.vhost_common.host_suffix, []
