# -*- coding: utf-8 -*-
u"""create spamassassin spamd configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio

_CONF_D = pkio.py_path('/var/lib/pgsql/data')

class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        # https://github.com/dinkel/docker-spamassassin/blob/master/Dockerfile
        self.buildt.require_component('docker')
        run_d = systemd.docker_unit_prepare(self)
'sa-update' && kill -HUP `cat /var/run/spamd.pid`
exec /usr/sbin/spamd -x --syslog-socket none --max-children $SPAMD_MAX_CHILDREN --helper-home-dir -u mail -g mail -p $SPAMD_PORT -i 0.0.0.0 -A $SPAMD_RANGE


sa-update -D

SPAMDOPTIONS='--daemonize --username=spamd --max-children=3 --socketpath=$SOCKET'


spamd --nouser-config \
    --syslog stderr \
    --pidfile /var/run/spamd.pid \
    --helper-home-dir /var/lib/spamd/db \
    --ip-address \
    --allowed-ips 0.0.0.0/0

--siteconfigpath=path
--listen=127.0.0.1
--ipv4-only
--port=

        systemd.docker_unit_enable(
            self,
            image='biviosoftware/perl',
            env=env,
            cmd='/var/lib/',
        )
        self.install_access(mode='700', owner=self.hdb.rsconf_db_run_u)
        self.install_directory(env.RABBITMQ_LOG_BASE)
        self.install_directory(env.RABBITMQ_MNESIA_BASE)
        for f in ('enabled_plugins', 'rabbitmq.config'):
            self.install_resource('rabbitmq/' + f, {}, run_d.join(f))
