# -*- coding: utf-8 -*-
u"""Build the tree

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio


class T(pkcollections.Dict):

    def __init__(self, dbt, host):
        super(T, self).__init__({
            components=pkcollections.Dict(),
            components_required=[],
            dbt=dbt,
            hdb=dbt.host_db(),
        })

    def create_host(self):
        dst_d = self.hdb.dst_d
        new = dst_d + '-new'
        old = dst_d + '-old'
        pkio.unchecked_remove(new, old)
        self.require_component(self.hdb.components)
        self.write_root_bash(
            '000.sh',
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
            self.components[c] = component.create(c, self)
            self.components[c].build()
            self.components_required.append(c)

    def write_root_bash(self, basename, lines):
        # python and perl scripts?
        pkio.write_text(
            self.dst.join(basename + '.sh'),
            '\n'.join(['#!/bin/bash'] + lines) + '\n',
        )


def default_command():
    """Build the distribution tree"""
    from rsconf import db

    dbt = db.T()
    for host in dbt.host_list():
        T(dbt, host).create_host()
