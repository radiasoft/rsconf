# -*- coding: utf-8 -*-
u"""host manipulation

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcli
from pykern import pkcollections
from pykern import pkjson


def init(host):
    from rsconf import db

    host = host.lower()
    dbt = db.T()
    for c, hosts in pkcollections.map_items(dbt.channel_hosts()):
        for h in hosts:
            if h == host.lower():
                return _host_init(dbt, c, h)
    pkcli.command_error('{}: host not found in rsconf_db', host)


def _host_init(dbt, channel, host):
    from rsconf.component import rsconf

    hdb = dbt.host_db(channel, host)
    return rsconf.host_init(hdb, host)
