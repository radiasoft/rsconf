# -*- coding: utf-8 -*-
"""host manipulation

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcli
from pykern import pkjson


def init(host):
    from rsconf.component import rsconf

    return _init_do(host, rsconf)


def init_docker_registry(host):
    from rsconf.component import docker_registry

    return _init_do(host, docker_registry)


def _init_do(host, comp):
    from rsconf import db

    host = host.lower()
    dbt = db.T()
    for c, hosts in dbt.channel_hosts().items():
        for h in hosts:
            if h == host.lower():
                return comp.host_init(dbt.host_db(c, h), h)
    pkcli.command_error("{}: host not found in rsconf_db", host)
