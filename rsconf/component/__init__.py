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
            buildt=buildt,
            hdb=buildt.hdb,
            name=name,
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
        self._install_access = pkcollections.Dict(
            mode='400',
            owner=self.hdb.guest_u,
            group=self.hdb.guest_u,
        )

    def install_access(self, mode=None, owner=None, group=None):
        if not mode is None:
            assert _MODE_RE.search(mode), \
                '{}: invalid mode'.format(mode)
            self._install_access.mode = mode
        if owner:
            self._install_access.owner = owner
        if group:
            self._install_access.group = group
        elif owner:
            self._install_access.group = owner
        self.root_bash.append(
            "rsconf_install_access '{mode}' '{owner}' '{group}'".format(**self._install_access),
        )

    def install_directory(self, host_path):
        assert int(self._install_access.mode, 8) & 0700 == 0700, \
            '{}: directory must be at least 700 mode (u=rwx)'
        self._bash_append(host_path, is_file=False)

    def install_resource(self, name, jinja_values, host_path):
        from pykern import pkjinja

        dst = self._bash_append_and_dst(host_path)
        dst.write(
            pkjinja.render_resource('name', values=jinja_values),
        )

    def install_secret(self, filename, host_path):
        dst = self._bash_append_and_dst(host_path)
        hdb.secret_d.join(filename).copy(dst, mode=True)

    def _bash_append(self, host_path, is_file=True):
        assert not "'" in host_path, \
            "{}: host_path contains single quote (')".format(rel_path)
        self.root_bash.append(
            "rsconf_install_{} '{}'".format(
                'file' if is_file else 'directory',
                host_path,
            ),
        )

    def _bash_append_and_dst(self, host_path):
        self._bash_append(host_path)
        dst = self.hdb.dst_d.join(host_path)
        assert not dst.check(), \
            '{}: dst already exists'.format(dst)
        return dst


def create_t(name, buildt):
    """Instantiate component

    Args:
        name (str): component to load
    Returns:
        module: component instance
    """
    import importlib

    return importlib.import_module('.' + name, __name__).T(name, buildt)
