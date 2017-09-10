# -*- coding: utf-8 -*-
u"""Load components

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
import re

_DONE = 'done'
_START = 'start'
_MODE_RE = re.compile(r'^\d{3,4}$')

class T(pkcollections.Dict):

    def __init__(self, name, buildt):
        super(T, self).__init__(
            name=name,
            buildt=buildt,
            state=_START,
        )

    def assert_done(self):
        assert self.state == _DONE, \
            '{}: invalidate state for component.{}'.format(self.state, self.name)

    def build(self):
        self.root_bash = [self.name + '() {'],
        self.internal_build(self)
        self.root_bash.append('}')
        self.buildt.write_root_bash(self.name, self.root_bash)
        self.state = _DONE
        self.install_access = pkcollections.Dict(
            mode='400',
            owner=self.build_ctx.run_user,
            group=self.build_ctx.run_user,
        )

    def install_access(self, mode=None, owner=None, group=None):
        if not mode is None:
            assert _MODE_RE.search(mode), \
                '{}: invalid mode'.format(mode)
            self.install_access.mode = mode
        if owner:
            self.install_access.owner = owner
        if group:
            self.install_access.group = group
        elif owner:
            self.install_access.group = owner
        self.root_bash.append(
            "rsconf_install_access '{mode}' '{owner}' '{group}'".format(**self.install_access),
        )

    def install_resource(self, name, jinja_values, rel_path):
        from pykern import pkjinja

        rel_path = str(rel_path)
        if rel_path.startswith('/'):
            rel_path = rel_path[1:]
        assert not "'" in rel_path, \
            "{}: rel_path contains single quote (')".format(rel_path)
        self.root_bash.append("rsconf_install '{}'".format(rel_path))
        dst = compt.buildt.dst_d.join(rel_path)
        assert not dst.check(), \
            '{}: dst already exists'.format(dst)
        dst.write(
            pkjinja.render_resource('name', values=jinja_values),
        )


def create_t(name, buildt):
    """Instantiate component

    Args:
        name (str): component to load
    Returns:
        module: component instance
    """
    import importlib

    return importlib.import_module('.' + name, __name__).T(name, buildt)
