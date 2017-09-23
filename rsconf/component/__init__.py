# -*- coding: utf-8 -*-
u"""Load components

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio
from pykern.pkdebug import pkdp, pkdc
import re

VISIBILITY_LIST = ('global', 'channel', 'host')
VISIBILITY_DEFAULT = VISIBILITY_LIST[1]

_DONE = 'done'
_START = 'start'
_MODE_RE = re.compile(r'^\d{3,4}$')
_BASH_FUNC_SUFFIX = '_rsconf_component'

class T(pkcollections.Dict):

    def __init__(self, name, buildt):
        super(T, self).__init__(
            buildt=buildt,
            hdb=buildt.hdb,
            name=name,
            state=_START,
        )

    def append_root_bash(self, *line):
        self._root_bash.extend(line)

    def append_root_bash_with_resource(self, script, jinja_values, bash_func):
        from pykern import pkjinja

        v = pkjinja.render_resource(script, values=jinja_values)
        self._root_bash_aux.append(v)
        self.append_root_bash(bash_func)

    def assert_done(self):
        assert self.state == _DONE, \
            '{}: invalidate state for component.{}'.format(self.state, self.name)

    def build(self):
        self.state = _DONE
        self._install_access = pkcollections.Dict()
        self._root_bash = [self.name + _BASH_FUNC_SUFFIX + '() {']
        self._root_bash_aux = []
        self.internal_build()
        self.append_root_bash('}')
        self._root_bash.extend(self._root_bash_aux)
        self.buildt.write_root_bash(self.name, self._root_bash)

    def install_access(self, mode=None, owner=None, group=None):
        if not mode is None:
            assert not isinstance(mode, int), \
                '{}: mode must be a string, not int'.format(mode)
            assert _MODE_RE.search(mode), \
                '{}: invalid mode'.format(mode)
            self._install_access.mode = mode
        if owner:
            self._install_access.owner = owner
        if group:
            self._install_access.group = group
        elif owner:
            self._install_access.group = owner
        self.append_root_bash(
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
            pkjinja.render_resource(name, values=jinja_values),
        )

    def install_secret(self, basename, host_path, gen_secret=None, visibility=VISIBILITY_DEFAULT):
        dst = self._bash_append_and_dst(host_path)
        src = self.hdb.secret_d.join(
            self._secret_base(self, basename, visibility),
        )
        if not src.check():
            assert gen_secret, \
                '{}: unable to generate secret: {}'.format(src, host_path)
            pkio.mkdir_parent_only(src)
            gen_secret(src)
        src.copy(dst, mode=True)

    def _bash_append(self, host_path, is_file=True):
        assert not "'" in str(host_path), \
            "{}: host_path contains single quote (')".format(host_path)
        self.append_root_bash(
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
        pkio.mkdir_parent_only(dst)
        return dst

    def _secret_base(self, basename, visibility):
        if visibility == VISIBILITY_LIST[0]:
            return basename
        assert visibility in VISIBILITY_LIST, \
            '{}: invalid visibility, must be {}'.format(
                visibility,
                VISIBILITY_LIST,
            )
        return '{}-{}'.format(basename, self.hdb[visibility])


def create_t(name, buildt):
    """Instantiate component

    Args:
        name (str): component to load
    Returns:
        module: component instance
    """
    import importlib

    return importlib.import_module('.' + name, __name__).T(name, buildt)
