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


class T(component.T):
    def internal_build(self):
        from rsconf import systemd

        if self.name == 'bop':
            self.buildt.require_component('docker', 'postgresql', 'nginx', 'postfix')
            self.append_root_bash(': nothing for now')
            for n in sorted(self.hdb.bop_apps):
                self.buildt.build_component(T(n, self.buildt))
            return
        j2_ctx = pkcollections.Dict(self.hdb)
        j2_ctx.bop_app_name = self.name
        r = re.compile('^' + self.name + '_(.+)')
        for k, v in j2_ctx.items():
            m = r.search(k)
            if m:
                j2_ctx['bop_' + m.group(1)] = v
        run_d = systemd.docker_unit_prepare(self)
        self.install_access(mode='700', owner=self.hdb.rsconf_db_run_u)
        self.install_directory(run_d)
        j2_ctx.bop_run_d = run_d
        volumes = ['/var/run/postgresql/.s.PGSQL.5432']
        for host_d, guest_d in (
            # POSIT: /etc/bivio.bconf has same values
            ('log', '/var/log/httpd'),
            ('db', '/var/db/bop'),
            ('bkp', '/var/bkp/bop'),
            ('logbop', '/var/log/bop'),
        ):
            x = run_d.join(host_d)
            j2_ctx['bop_{}_host_d'.format(host_d)] = x
            self.install_directory(x)
            volumes.append([x, guest_d])
        self.install_access(mode='400')
        for host_f, guest_f in (
            ('httpd.conf', '/etc/httpd/conf/httpd.conf'),
            ('bivio.bconf', '/etc/bivio.bconf')
        ):
            x = run_d.join(host_f)
            self.install_resource('bop/' + host_f, j2_ctx, x)
            volumes.append([x, guest_f])
        systemd.docker_unit_enable(
            self,
            image=j2_ctx.bop_docker_image,
            env=pkcollections.Dict(),
            cmd='/usr/sbin/httpd -DFOREGROUND',
            volumes=volumes,
        )
        # After the unit files are installed
        self.append_root_bash_with_resource(
            'bop/initdb.sh',
            j2_ctx,
            j2_ctx.bop_app_name + '_initdb',
        )
        _install_vhosts(self, j2_ctx)


def _install_vhosts(self, j2_ctx):
    from rsconf.component import nginx

    def _domain(vh):
        res = vh.get('domain')
        if res:
            return res
        return vh.get('facade') + '.' + j2_ctx.bop_vhost_common_host_suffix

    for vh in j2_ctx.bop_vhosts:
        h = _domain(vh)
        j2_ctx.bop_http_redirects = []
        j2_ctx.bop_https_redirects = []
        # mail_domain
        # aliases
        nginx.install_vhost(self, vhost=h, resource_d='bop', j2_ctx=j2_ctx)
