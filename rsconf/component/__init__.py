# -*- coding: utf-8 -*-
u"""Load components

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio
from pykern.pkdebug import pkdp, pkdc
import re

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

    def append_root_bash_with_resource(self, script, j2_ctx, bash_func):
        from pykern import pkjinja

        v = pkjinja.render_resource(script, j2_ctx, strict_undefined=True)
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

    def install_abspath(self, abs_path, host_path):
        dst = self._bash_append_and_dst(host_path)
        abspath.copy(dst, mode=True)

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

    def install_resource(self, name, j2_ctx, host_path):
        from pykern import pkjinja

        dst = self._bash_append_and_dst(host_path)
        dst.write(
            pkjinja.render_resource(name, j2_ctx, strict_undefined=True),
        )

    def install_secret_path(self, filename, host_path, gen_secret=None, visibility=None):
        from rsconf import db

        dst = self._bash_append_and_dst(host_path)
        src = db.secret_path(self.hdb, filename, visibility=visibility)
        if not src.check():
            assert gen_secret, \
                '{}: unable to generate secret: {}'.format(src, host_path)
            pkio.mkdir_parent_only(src)
            gen_secret(src)
        src.copy(dst, mode=True)

    def install_tls_key_and_crt(self, domain, dst_d):
        kc = tls_key_and_crt(hdb, domain)
        dst = pkcollections.Dict(
            key=dst_d.join(kc.key.basename),
            crt=dst_d.join(kc.crt.basename),
        )
        self.install_abspath(kc.key, dst.key)
        self.install_abspath(kc.crt, dst.crt)
        return dst



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
        dst = self.hdb.build_dst_d.join(host_path)
        assert not dst.check(), \
            '{}: dst already exists'.format(dst)
        pkio.mkdir_parent_only(dst)
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


def tls_key_and_crt(hdb, domain):
    from rsconf.pkcli import tls
    from rsconf import db

    #TODO(robnagler) wildcard: search for name if single domain, then
    #  wildcard file
    #TODO(robnagler) search for MDC
    base = domains[0]
    src = db.secret_path(hdb, base, visibility='global')
    src_key = src + tls.KEY_EXT
    src_crt = src + tsl.CRT_EXT
    if not src_crt.check():
        assert pkconfig.channel_in_internal_test(channel=hdb.rsconf_db_channel), \
            '{}: missing crt for: {}'.format(src_crt, domains)
        pkio.mkdir_parent_only(src_crt)
        tls.gen_self_signed_crt(src, *domains)
    assert src_key.check(), \
        '{}: missing key for: {}'.format(src_key, domains)
    return pkcollections.Dict(key=src_key, crt=src_crt)
