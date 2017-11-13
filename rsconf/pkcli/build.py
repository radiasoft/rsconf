# -*- coding: utf-8 -*-
u"""Build the tree

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio
from pykern.pkdebug import pkdp, pkdc


class T(pkcollections.Dict):

    def __init__(self, dbt, channel, host):
        super(T, self).__init__(
            components=pkcollections.Dict(),
            components_required=[],
            dbt=dbt,
            hdb=dbt.host_db(channel, host),
        )

    def create_host(self):
        dst_d = self.hdb.rsconf_db_srv_host_d.join(self.hdb.rsconf_db_host)
        new = dst_d + '-new'
        self.hdb.build_dst_d = new
        old = dst_d + '-old'
        pkio.unchecked_remove(new, old)
        pkio.mkdir_parent(new)
        self.require_component(*self.hdb.rsconf_db_components)
        self.write_root_bash(
            '000',
            ['rsconf_require ' + x for x in self.components_required],
        )
        if dst_d.check():
            dst_d.rename(old)
        else:
            old = None
        new.rename(dst_d)
        if old:
            pkio.unchecked_remove(old)


    def require_component(self, *components):
        from rsconf import component

        for c in components:
            compt = self.components.get(c)
            if compt:
                compt.assert_done()
                continue
            self.components[c] = component.create_t(c, self)
            self.components[c].build()
            self.components_required.append(c)

    def write_root_bash(self, basename, lines):
        # python and perl scripts?
        pkio.write_text(
            self.hdb.build_dst_d.join(basename + '.sh'),
            '\n'.join(['#!/bin/bash'] + lines) + '\n',
        )


def default_command():
    """Build the distribution tree"""
    from rsconf import db

    if pkconfig.channel_in('dev'):
        db.setup_dev()
    dbt = db.T()
    for c, hosts in pkcollections.map_items(dbt.channel_hosts()):
        for h in hosts:
            T(dbt, c, h).create_host()
