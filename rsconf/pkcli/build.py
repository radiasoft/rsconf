# -*- coding: utf-8 -*-
u"""Build the tree

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections


class T(pkcollections.Dict):

    def build_host(self):
        """Build one host"""
        from pykern import pkio

        self.require_component(self.dbt.zdb[host].components)
        self.write_root_bash(
            '000.sh',
            ['rsconf_require ' + x for x in self.components_required],
        )

    def install_file(self, files, mode, owner, group=None):
        if not group:
            group = owner
        build_ctx.
        'rsconf_install_access {} {} {}'.format(mode, owner, group),

    def require_component(self, components):
        from rsconf import component

        for c in components:
            r = self.components_required.get(c)
            if r:
                assert r == 'done', \
                    '{}: invalidate state for component.{}'.format(r, c)
                continue
            self.components_required[c] = 'start'
            build_ctx.component_ctx[c].lines = [c + '() {']
            component.import_module(c).rsconf_build(self)
            build_ctx.component_ctx[c].lines.append('}')
            self.write_root_bash(c, build_ctx.component_ctx[c].lines)
            self.components_required[c] = 'done'

    def write_root_bash(self, basename, lines):
        # python and perl scripts?
        pkio.write_text(
            self.dst.join(basename + '.sh'),
            '\n'.join(['#!/bin/bash'] + lines) + '\n',
        )


def default_command():
    """Build the distribution tree"""
    from rsconf import db
    from pykern import pkio

    dbt = db.T()
    srv_d = self.srv
    for host in db.keys():
        dst = self.srv.join(host)
        new = dst + '-new'
        old = dst + '-old'
        pkio.unchecked_remove(new, old)
        T(
            host=host,
            dbt=dbt,
            dst=dst,
            components_required=pkcollections.OrderedMapping(),
        ).build_host()
        if dst.check():
            dst.rename(old)
        else:
            old = None
        new.rename(dst)
        if old:
            pkio.unchecked_remove(old)
