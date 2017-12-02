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


class T(component.T):
    def internal_build(self):
        from rsconf import systemd

        if self.name == 'bop':
            self.buildt.require_component('docker')
            self.append_root_bash(': nothing for now')
            for n in sorted(self.hdb.bop_apps):
                self.buildt.build_component(T(n, self.buildt))
            return
        j2_ctx = pkcollections.Dict(self.hdb)
        r = re.compile('^' + self.name + '_(.+)')
        for k, v in j2_ctx.items():
            m = r.search(k)
            if m:
                j2_ctx['bop_' + m.group(1)] = v
        run_d = systemd.docker_unit_prepare(self)
        self.install_access(mode='700', owner=self.hdb.rsconf_db_run_u)
        self.install_directory(run_d)
        volumes = ['/var/run/postgresql/.s.PSGSQL.5432']
        for host_d, guest_d in (
            # POSIT: /etc/bivio.bconf has same values
            ('log', '/var/log/httpd'),
            ('db', '/var/db/bop'),
            ('bkp', '/var/bkp/bop'),
            ('logbop', '/var/log/bop'),
        ):
            x = run_d.join(host_d)
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
        # /var/lib/petshop/start bash
        # bivio sql init_dbms
