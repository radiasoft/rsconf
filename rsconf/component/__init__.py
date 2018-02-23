# -*- coding: utf-8 -*-
u"""Load components

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio
from pykern.pkdebug import pkdp, pkdc, pkdlog
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

    def append_root_bash_with_main(self, j2_ctx):
        self.append_root_bash_with_resource(
            '{}/main.sh'.format(self.name),
            j2_ctx,
            '{}_main'.format(self.name),
        )

    def append_root_bash_with_resource(self, script, j2_ctx, bash_func):
        v = _render_resource(script, j2_ctx)
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

    def install_abspath(self, abs_path, host_path, ignore_exists=False):
        dst = self._bash_append_and_dst(host_path, ignore_exists=ignore_exists)
        if dst:
            abs_path.copy(dst, mode=True)

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

    def install_symlink(self, old_host_path, new_host_path):
        new = new_host_path.bestrelpath(old_host_path)
        _assert_host_path(new)
        _assert_host_path(old_host_path)
        self.append_root_bash(
            "rsconf_install_symlink '{}' '{}'".format(old_host_path, new),
        )

    def install_resource(self, name, j2_ctx, host_path):
        dst = self._bash_append_and_dst(host_path)
        dst.write(_render_resource(name, j2_ctx))

    def install_secret_path(self, filename, host_path, gen_secret=None, visibility=None):
        from rsconf import db

        src = self.secret_path_value(filename, gen_secret, visibility)[1]
        dst = self._bash_append_and_dst(host_path)
        src.copy(dst, mode=True)

    def install_tls_key_and_crt(self, domain, dst_d):
        kc = tls_key_and_crt(self.hdb, domain)
        dst = pkcollections.Dict(
            key=dst_d.join(kc.key.basename),
            crt=dst_d.join(kc.crt.basename),
        )
        self.install_abspath(kc.key, dst.key, ignore_exists=True)
        self.install_abspath(kc.crt, dst.crt, ignore_exists=True)
        return dst

    def secret_path_value(self, filename, gen_secret=None, visibility=None):
        from rsconf import db

        src = db.secret_path(self.hdb, filename, visibility=visibility)
        if not src.check():
            assert gen_secret, \
                '{}: unable to generate secret: {}'.format(src)
            pkio.mkdir_parent_only(src)
            gen_secret(src)
        with open(str(src), 'rb') as f:
            return f.read(), src

    def service_prepare(self, watch_files, name=None):
        if not name:
            name = self.name
        self.append_root_bash(
            "rsconf_service_prepare '{}'".format(
                "' '".join([name] + list(str(w) for w in watch_files)),
            ),
        )

    def _bash_append(self, host_path, is_file=True):
        _assert_host_path(host_path)
        self.append_root_bash(
            "rsconf_install_{} '{}'".format(
                'file' if is_file else 'directory',
                host_path,
            ),
        )

    def _bash_append_and_dst(self, host_path, ignore_exists=False):
        self._bash_append(host_path)
        dst = self.hdb.build.dst_d.join(host_path)
        if dst.check():
            if ignore_exists:
                return None
            raise AssertionError('{}: dst already exists'.format(dst))
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

    base, domains = _find_tls_crt(hdb, domain)
    src = db.secret_path(hdb, base, visibility='global')
    src_key = src + tls.KEY_EXT
    src_crt = src + tls.CRT_EXT
    if not src_crt.check():
        assert hdb.component.tls_crt_create, \
            '{}: missing crt for: {}'.format(src_crt, domain)
        pkio.mkdir_parent_only(src_crt)
        tls.gen_self_signed_crt(*domains, basename=src)
    assert src_key.check(), \
        '{}: missing key for: {}'.format(src_key, domain)
    return pkcollections.Dict(key=src_key, crt=src_crt)


def _assert_host_path(host_path):
    assert not "'" in str(host_path), \
        "{}: host_path contains single quote (')".format(host_path)


def _find_tls_crt(hdb, domain):
    for crt, domains in hdb.component.tls_crt.items():
        if domain in domains:
            return crt, domains
    raise AssertionError('{}: tls crt for domain not found'.format(domain))


def _render_resource(name, j2_ctx):
    from pykern import pkjinja
    try:
        return pkjinja.render_resource(name, j2_ctx, strict_undefined=True)
    except Exception as e:
        pkdlog('{}: {}', name, e)
        raise
