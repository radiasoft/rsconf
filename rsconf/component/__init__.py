# -*- coding: utf-8 -*-
u"""Load components

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern import pkcompat
from pykern import pkconfig
from pykern import pkio
from pykern.pkdebug import pkdp, pkdc, pkdlog
import hashlib
import re
import subprocess

_DONE = 'done'
_START = 'start'
_MODE_RE = re.compile(r'^\d{3,4}$')
_BASH_FUNC_SUFFIX = '_rsconf_component'
TLS_SECRET_SUBDIR = 'tls'
_WILDCARD_TLS = 'star'

class T(PKDict):

    def __init__(self, name, buildt):
        super(T, self).__init__(
            buildt=buildt,
            hdb=buildt.hdb,
            name=name,
            state=_START,
        )

    def append_root_bash(self, *line):
        self._root_bash.extend(line)

    def append_root_bash_with_file(self, abs_path, j2_ctx):
        """Append lines from jinja-rendered path

        Distinct from `append_root_bash_with_resource`.

        Args:
            abs_path (py.path): absolute path of file to render
            j2_ctx (PKDict): dictionary to render
        """
        self._root_bash.append(self._render_file(abs_path, j2_ctx))

    def append_root_bash_with_main(self, j2_ctx):
        self.append_root_bash_with_resource(
            '{}/main.sh'.format(self.name),
            j2_ctx,
            '{}_main'.format(self.name),
        )

    def append_root_bash_with_resource(self, script, j2_ctx, bash_func):
        v = self._render_resource(script, j2_ctx)
        self._root_bash_aux.append(v)
        self.append_root_bash(bash_func)

    def assert_done(self):
        assert self.state == _DONE, \
            '{}: invalidate state for component.{}'.format(self.state, self.name)

    def build_compile(self):
        self.state = _DONE
        self._install_access = PKDict()
        self._root_bash = [self.name + _BASH_FUNC_SUFFIX + '() {']
        self._root_bash_aux = []
        if hasattr(self, 'internal_build_compile'):
            self.internal_build_compile()
            self.buildt.append_write_queue(self)
        else:
            self.internal_build()
            self.build_write()

    def build_write(self):
        self.internal_build_write()
        self.append_root_bash('}')
        self._root_bash.extend(self._root_bash_aux)
        self.buildt.write_root_bash(self.name, self._root_bash)

    def has_tls(self, j2_ctx, domain):
        try:
            _find_tls_crt(j2_ctx, domain)
            return True
        except AssertionError:
            return False

    def install_abspath(self, abs_path, host_path, ignore_exists=False):
        self._bash_append_and_dst(
            host_path,
            ignore_exists=ignore_exists,
            file_src=abs_path,
        )

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
        assert int(self._install_access.mode, 8) & 0o700 == 0o700, \
            '{}: directory must be at least 700 mode (u=rwx)'
        self._bash_append(host_path, is_file=False)

    def install_ensure_file_exists(self, host_path):
        self._bash_append(host_path, is_file=True, ensure_exists=True)

    def install_joined_lines(self, lines, host_path):
        """Write lines with newlines to host_path

        Args:
            lines (object): iterable
            host_path (py.path): where to install
        """
        p = self.tmp_path()
        p.write(''.join([x + '\n' for x in lines]))
        self.install_abspath(p, host_path)

    def install_perl_rpm(self, j2_ctx, rpm_base, channel=None):
        src = self.rpm_file(j2_ctx, rpm_base, channel)
        r = src.basename
        if r in self.hdb.component.setdefault('_installed_rpms', set()):
            return r
        self.hdb.component._installed_rpms.add(r)
        dst = j2_ctx.build.dst_d.join(r)
        dst.mksymlinkto(src, absolute=False)
        self.append_root_bash("rsconf_install_perl_rpm '{}' '{}' '{}'".format(
            rpm_base,
            r,
            pkcompat.from_bytes(
                subprocess.check_output(['rpm', '-qp',  str(src)]),
            ).strip(),
        ))
        return r

    def install_resource(self, name, j2_ctx, host_path=None):
        if not host_path:
            host_path = name
            if host_path.ext == '.sh':
                host_path = host_path.new(ext='')
            name = self.name + '/' + name.basename
        self._bash_append_and_dst(
            host_path,
            file_contents=self._render_resource(name, j2_ctx),
        )

    def install_secret_path(self, filename, host_path, gen_secret=None, visibility=None):
        src = self.secret_path_value(filename, gen_secret, visibility)[1]
        dst = self._bash_append_and_dst(host_path, file_src=src)

    def install_symlink(self, old_host_path, new_host_path):
        _assert_host_path(new_host_path)
        rel = new_host_path.bestrelpath(old_host_path)
        _assert_host_path(old_host_path)
        self.append_root_bash(
            "rsconf_install_symlink '{}' '{}'".format(rel, new_host_path),
        )

    def install_tls_key_and_crt(self, domain, dst_d):
        kc = tls_key_and_crt(self.hdb, domain)
        dst = PKDict(
            key=dst_d.join(kc.key.basename),
            crt=dst_d.join(kc.crt.basename),
        )
        self.install_abspath(kc.key, dst.key, ignore_exists=True)
        self.install_abspath(kc.crt, dst.crt, ignore_exists=True)
        return dst

    def internal_build_write(self):
        """Called after internal_build_compile"""
        pass

    def j2_ctx_init(self):
        self.j2_ctx = self.hdb.j2_ctx_copy()
        return self.j2_ctx, self.j2_ctx.setdefault(self.name, PKDict())

    def j2_ctx_pksetdefault(self, defaults):
        """Set defaults on self.j2_ctx

        defaults is nested dicts with dotted keys that
        will be turned into nested `PKDict` if not defined.

        Uses PKDictpksetdefault to set values so can use
        callables as initializers.

        Args:
            defaults (dict): nested values
        """
        def f(prefix, defaults):
            for k, v in defaults.items():
                k = prefix + k.split('.')
                if isinstance(v, dict):
                    f(k, v)
                    continue
                n = self.j2_ctx
                for y in k[:-1]:
                    n = n.setdefault(y, PKDict())
                n.pksetdefault(k[-1], v)

        f([], defaults)

    def rpm_file(self, j2_ctx, rpm_base, channel=None):
        s = j2_ctx.rsconf_db.rpm_source_d.join(
            '{}-{}.rpm'.format(
                rpm_base,
                channel or j2_ctx.rsconf_db.channel,
            ),
        )
        assert s.check(), \
            '{}: rpm does not exist'.format(s)
        return s

    def proprietary_file(self, j2_ctx, file_base, channel=None):
        s = j2_ctx.rsconf_db.proprietary_source_d.join(
            '{}-{}.tar.gz'.format(
                file_base,
                channel or j2_ctx.rsconf_db.channel,
            ),
        )
        assert s.check(), \
            '{}: file does not exist'.format(s)
        return s

    def rsconf_append(self, path, line_or_grep, line=None):
        l = "rsconf_edit_no_change_res=0 rsconf_append '{}' '{}'".format(path, line_or_grep)
        if not line is None:
            l += " '{}'".format(line)
        self.append_root_bash(l)

    def rsconf_edit(self, path, egrep, perl):
        self.append_root_bash(
            "rsconf_edit_no_change_res=0 rsconf_edit '{}' '{}' '{}'".format(
                path,
                egrep,
                perl,
            ),
        )

    def rsconf_service_restart(self):
        self.append_root_bash('rsconf_service_restart')

    def rsconf_service_restart_at_end(self):
        self.append_root_bash(
            "rsconf_service_restart_at_end '{}'".format(self.name),
        )

    def secret_path_value(self, filename, gen_secret=None, visibility=None):
        from rsconf import db

        src = db.secret_path(self.hdb, filename, visibility=visibility)
        if src.check():
            return pkio.read_text(src), src
        assert gen_secret, \
            'unable to generate secret: path={}'.format(src)
        res = gen_secret()
        res = pkcompat.from_bytes(self._write_binary(src, res))
        return res, src

    def service_prepare(self, watch_files, name=None):
        if not name:
            name = self.name
        self.append_root_bash(
            "rsconf_service_prepare '{}'".format(
                "' '".join([name] + list(str(w) for w in watch_files)),
            ),
        )

    def tmp_path(self):
        from rsconf import db

        return self.hdb.rsconf_db.tmp_d.join(db.random_string())


    def _bash_append(self, host_path, is_file=True, ensure_exists=False, md5=None):
        _assert_host_path(host_path)
        if is_file:
            op = 'ensure_file_exists' if ensure_exists else 'file'
            if md5:
                md5 = " '{}'".format(md5)
        else:
            assert not ensure_exists, \
                '{}: do not pass ensure_exists for directories'.format(host_path)
            assert not md5, \
                '{}: do not pass md5 for directories'.format(host_path)
            op = 'directory'
        if not md5:
            md5 = ''
        self.append_root_bash(
            "rsconf_install_{} '{}'{}".format(op, host_path, md5),
        )

    def _bash_append_and_dst(self, host_path, ignore_exists=False, file_contents=None, file_src=None):
        dst = self.hdb.build.dst_d.join(host_path)
        if dst.check():
            if ignore_exists:
                return None
            raise AssertionError('{}: dst already exists'.format(dst))
        pkio.mkdir_parent_only(dst)
        md5 = None
        if file_src:
            assert file_contents is None, \
                '{}: do not pass both file_contents and file_src'.format(host_path)
            file_contents = file_src.read_binary()
        if file_contents:
            md5 = _md5(self._write_binary(dst, file_contents))
        self._bash_append(host_path, md5=md5)
        return dst

    def _render_file(self, path, j2_ctx):
        from pykern import pkjinja

        try:
            return pkjinja.render_file(path, j2_ctx, strict_undefined=True)
        except Exception as e:
            pkdlog('path={} exception={}', path, e)
            raise

    def _render_resource(self, name, j2_ctx):
        from pykern import pkjinja
        from rsconf import db

        return self._render_file(
            db.resource_path(j2_ctx, name + pkjinja.RESOURCE_SUFFIX),
            j2_ctx,
        )

    def _write_binary(self, path, data):
        """Write as binary to Linux file

        Any strings must be convertable to ascii. Since this is a configuration management
        system, we have control over this.

        Args:
            path (py.path): will use write()
            data (object): if not bytes, will encode with ascii

        Returns:
            bytes: data (possibly converted)
        """
        if not isinstance(data, bytes):
            data = data.encode('ascii')
        path.write(data, mode='wb', ensure=True)
        return data


def create_t(name, buildt):
    """Instantiate component

    Args:
        name (str): component to load
    Returns:
        module: component instance
    """
    import importlib

    return importlib.import_module('.' + name, __name__).T(name, buildt)


def tls_key_and_crt(j2_ctx, domain):
    from rsconf.pkcli import tls
    from rsconf import db

    src, domains = _find_tls_crt(j2_ctx, domain)
    src_key = src + tls.KEY_EXT
    src_crt = src + tls.CRT_EXT
    if not src_crt.check():
        assert j2_ctx.component.tls_crt_create, \
            '{}: missing crt for: {}'.format(src_crt, domain)
        pkio.mkdir_parent_only(src_crt)
        # https://stackoverflow.com/a/42730929
        # Cannot pass (basename=str(src), *domains)
        tls.gen_self_signed_crt(str(src), *domains)
    assert src_key.check(), \
        '{}: missing key for: {}'.format(src_key, domain)
    return PKDict(key=src_key, crt=src_crt)


def _assert_host_path(host_path):
    assert not "'" in str(host_path), \
        "{}: host_path contains single quote (')".format(host_path)


def _find_tls_crt(j2_ctx, domain):
    from rsconf.pkcli import tls
    from rsconf import db

    d = db.secret_path(j2_ctx, TLS_SECRET_SUBDIR, visibility='global')
    for crt, domains in j2_ctx.component.tls_crt.items():
        if domain in domains:
            return d.join(crt), domains
    for s in (
        domain,
        domain.replace('.', '_'),
        '.'.join([_WILDCARD_TLS] + domain.split('.')[1:]),
        # sirepo.com is in wildcard cert star.sirepo.com
        _WILDCARD_TLS + '.' + domain,
    ):
        src = d.join(s)
        # due to dots in domain, we can't use ext=
        if (src + tls.KEY_EXT).check():
            return src, domain
    assert j2_ctx.component.tls_crt_create, \
        f'{domain}: tls crt for domain not found'
    src = d.join(domain)
    pkio.mkdir_parent_only(src)
    tls.gen_self_signed_crt(str(src), *domain)
    return src, domain


def _md5(data):
    m = hashlib.md5()
    m.update(data)
    return pkcompat.from_bytes(m.hexdigest())
