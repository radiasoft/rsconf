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
import os
import pwd


class T(pkcollections.Dict):

    def __init__(self, dbt, channel, host):
        super(T, self).__init__(
            components=pkcollections.Dict(),
            components_required=[],
            dbt=dbt,
            hdb=dbt.host_db(channel, host),
        )

    def build_component(self, compt_or_name):
        from rsconf import component

        if isinstance(compt_or_name, component.T):
            compt = compt_or_name
            assert not self.components.get(compt.name), \
                '{}: duplicate component'.format(compt.name)
        else:
            compt = self.components.get(compt_or_name)
            if compt:
                compt.assert_done()
                return
            compt = component.create_t(compt_or_name, self)
        self.components[compt.name] = compt
        compt.build()
        # Must be after, since write_root_bash happens from this list and
        # dependencies in build() must come first
        self.components_required.append(compt.name)

    def create_host(self):
        prev_umask = None
        try:
            prev_umask = os.umask(022)
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
            u = self.hdb.rsconf_db_srv_u
            if pwd.getpwuid(os.getuid())[0] != u:
                new.chown(u, u, rec=True)
            new.rename(dst_d)
            if old:
                pkio.unchecked_remove(old)
        finally:
            if prev_umask:
                os.umask(prev_umask)


    def require_component(self, *components):
        from rsconf import component

        for c in components:
            self.build_component(c)

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
        from rsconf.pkcli import setup_dev

        setup_dev.default_command()

    dbt = db.T()
    for c, hosts in pkcollections.map_items(dbt.channel_hosts()):
        for h in hosts:
            T(dbt, c, h).create_host()
