# -*- coding: utf-8 -*-
u"""host manipulation

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

def init(host):
    from rsconf import db

    host = host.lower()
    dbt = db.T()
    for c, hosts in pkcollections.map_items(dbt.channel_hosts()):
        for h in hosts:
            if h == host.lower():
                return _init_host(dbt, c, h)
    pkcli.command_error('{}: host not found in rsconf_db', host)


def _init_host(dbt, channel, host):
    import rsconf import db

    hdb = dbt.host_db(channel, host)
    jf = db.secret_path(hdb, hdb.rsconf_db., visibility=_PASSWD_VISIBILITY)
    if jf.check():
        with jf.open() as f:
            y = pkjson.load_any(f)
    else:
        y = pkcollections.Dict()
    assert not host in y, \
        '{}: host already exists'
    y[host] = db.random_string()
    pkjson.dump_pretty(y, filename=jf)
    pf = db.secret_path(hdb, _PASSWD_SECRET_F, visibility=_PASSWD_VISIBILITY)
    with pf.open(mode='a') as f:
        f.write('{}:{}\n'.format(host, bcrypt.hashpw(y[host], bcrypt.gensalt(5))))
