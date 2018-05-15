# -*- coding: utf-8 -*-
u"""create bivio_named configuration

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import network
        from rsconf.component import bop

        self.buildt.require_component('base_all')
        # need bind installed
        self.append_root_bash('rsconf_yum_install bind')
        j2_ctx = self.hdb.j2_ctx_copy()
        network.update_j2_ctx(j2_ctx)
        rpm = self.install_perl_rpm(j2_ctx, 'bivio-named')
        run_d = systemd.custom_unit_prepare(self, j2_ctx, [rpm])
        j2_ctx.setdefault('bivio_named', pkcollections.Dict()).update(
            dbdir=run_d.join('db'),
            etc=run_d.join('etc'),
        )
        z = j2_ctx.bivio_named
        z.listen_on = '127.0.0.1;'
        ip = j2_ctx.network.get('primary_public_ip', '')
        if ip:
            z.listen_on += ' ' + ip + ';'
        else:
            assert j2_ctx.rsconf_db.channel == 'dev', \
                'primary_public_ip: must have a public ip to run named'
        z.run_group = 'named'
        # Default is 10K+
        z.setdefault('max_sockets', 1024)
        # Default is number of cores, which is ridiculous
        z.setdefault('num_threads', 4)
        z.run_u = j2_ctx.rsconf_db.root_u
        # POSIT: same directory in build in rpm-perl/radiasoft-download.sh
        z.db_d = run_d.join('db')
        # POSIT: same file in rpm-perl/radiasoft-download.sh
        z.zones_f = z.db_d.join('zones.conf')
        z.conf_f = run_d.join('named.conf')
        # Needs to be there before rpms
        systemd.custom_unit_enable(
            self,
            j2_ctx,
            run_u=z.run_u,
            run_group=z.run_group,
            run_d_mode='710',
        )
        z.stats_f = j2_ctx.systemd.runtime_d.join('bind.stats')
        z.session_key_f = j2_ctx.systemd.runtime_d.join('session.key')
        z.run_u = j2_ctx.rsconf_db.root_u
        self.install_access(mode='750', owner=z.run_u, group=z.run_group)
        self.install_directory(z.db_d)
        self.install_access(mode='440')
        self.install_resource('bivio_named/named.conf', j2_ctx, z.conf_f)
