# -*- coding: utf-8 -*-
u"""create bop apps for a host

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import re
from pykern.pkdebug import pkdp
from rsconf import component
from pykern import pkcollections
from pykern import pkconfig


SOURCE_CODE_D = '/usr/share/Bivio-bOP-src'

COMMON_RPMS = ('bivio-perl.rpm', 'perl-Bivio.rpm')

class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf import db
        from rsconf.component import logrotate
        from rsconf.component import nginx

        if self.name == 'bop':
            self.hdb.bop.mail_domains = pkcollections.Dict()
            self.hdb.bop.aux_directives = ''
            self.buildt.require_component('postgresql', 'nginx', 'postfix')
            for n in sorted(self.hdb.bop.apps):
                vhostt = T(n, self.buildt)
                vhostt.bopt = self
                self.buildt.build_component(vhostt)
            j2_ctx = self.hdb.j2_ctx_copy()
            z = j2_ctx.bop
            z.mail_domain_keys = sorted(self.hdb.bop.mail_domains.keys())
            nginx.update_j2_ctx_and_install_access(self, j2_ctx)
            self.install_resource(
                'bop/nginx_common.conf',
                j2_ctx,
                nginx.CONF_D.join('bop_common.conf'),
            )
            self.append_root_bash_with_main(j2_ctx)
            return
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.bop
        rpms = list(COMMON_RPMS)
        z.run_u = j2_ctx.rsconf_db.run_u
        z.app_name = self.name
        db.merge_dict(z, j2_ctx[self.name])
        r = None if z.perl_root = 'Bivio::PetShop' else 'perl-{}.rpm'.format(z.perl_root)
        run_d = custom_unit_prepare(self, j2_ctx, app_rpm=r)
        z.conf_f = run_d.join('httpd.conf')
        z.bconf_f = run_d.join('bivio.bconf')
        z.log_postrotate_f = run_d.join('reload')
        z.http_cmd = "/usr/sbin/httpd -d '{}' -f '{}'".format(z.run_d, z.conf_f)
        z.source_code_d = SOURCE_CODE_D
        z.run_d = run_d
        systemd.custom_unit_enable(
            self,
            start='start',
            reload='reload',
            stop='stop',
            resource_d='bop',
            run_u=z.run_u,
        )
        self.install_access(mode='700', owner=z.run_u)
        for d in 'bkp', 'db', 'log', 'logbop':
            x = run_d.join(d)
            z['{}_d'.format(d)] = x
            self.install_directory(x)
        self.install_access(mode='400')
        self.install_resource('bop/httpd.conf', j2_ctx, z.conf_f)
        self.install_resource('bop/bivio.bconf', j2_ctx, z.bconf_f)
        self.install_access(mode='500')
        logrotate.install_conf(self, j2_ctx, resource_d='bop')
        # After the unit files are installed
        self.append_root_bash_with_resource(
            'bop/initdb.sh',
            j2_ctx,
            z.app_name + '_initdb',
        )
        self.bopt.hdb.bop.aux_directives += j2_ctx.get('bop.nginx_aux_directives', '')
        _install_vhosts(self, j2_ctx)


def custom_unit_prepare(compt, j2_ctx, app_rpm=None):
    from rsconf import systemd
    watch = []
    for r in COMMON_RPMS + (app_rpm,):
        if not r:
            continue
        watch.append(r)
        compt.install_rpm(r)
    return systemd.custom_unit_prepare(compt, *watch)

def _install_vhosts(self, j2_ctx):
    from rsconf.component import nginx

    def _domain(vh):
        res = vh.get('domains')
        if res:
            return res[0], res[1:]
        return vh.get('facade') + '.' + j2_ctx.bop.vhost_common.host_suffix, []

    for vh in j2_ctx.bop.vhosts:
        h, j2_ctx.bop.domain_aliases = _domain(vh)
        j2_ctx.bop.aux_directives = vh.get('nginx_aux_directives', '')
        nginx.install_vhost(
            self,
            vhost=h,
            backend_host=j2_ctx.rsconf_db.host,
            backend_port=j2_ctx.bop.listen_base + 1,
            resource_d='bop',
            j2_ctx=j2_ctx,
        )
        for m in vh.get('mail_domains', []):
            self.bopt.hdb.bop.mail_domains[m] = j2_ctx.bop.listen_base
