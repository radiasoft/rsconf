# -*- coding: utf-8 -*-
u"""create spamassassin spamd configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio


class T(component.T):

    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import network
        from rsconf.component import logrotate
        from rsconf.component import bop

        self.buildt.require_component('base_all')
        jc = self.hdb.j2_ctx_copy()
        z = jc.spamd
        conf_d = pkio.py_path('/etc/mail/spamassassin')
        nc = self.buildt.get_component('network')
        z.sa_update_keys_d = conf_d.join('sa-update-keys')
        z.trusted_networks = ' '.join(nc.trusted_nets())
        watch = bop.install_perl_rpms(self, jc) + [conf_d]
        systemd.custom_unit_prepare(self, jc, watch)
        socket_d = pkio.py_path('/run/spamd')
        z.socket_path = pkio.py_path('/run/spamd/spamd.sock')
        self.install_access(mode='755', owner=jc.rsconf_db.run_u)
        self.install_directory(conf_d)
        self.install_directory(socket_d)
        self.install_access(mode='444')
        self.install_resource(
            'spamd/spamc.conf',
            jc,
            conf_d.join('spamc.conf'),
        )
        logrotate.install_conf(self, jc)
        self.append_root_bash_with_main(jc)
        systemd.custom_unit_enable(self, jc)
