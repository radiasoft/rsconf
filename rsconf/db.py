# -*- coding: utf-8 -*-
u"""Database

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio
from pykern.pkdebug import pkdc, pkdp

_ZERO_YML = '000.yml'
_SRV_SUBDIR = 'srv'
_DEFAULT_DB_SUBDIR = 'run'
_SECRET_SUBDIR = 'secret'
_NGINX_SUBDIR = 'nginx'
_HOST_SUBDIR = 'host'
_LEVELS = ('default', 'channel', 'host')

class T(pkcollections.Dict):

    def __init__(self, *args, **kwargs):
        from pykern import pkyaml

        super(T, self).__init__(*args, **kwargs)
        self.base = pkyaml.load_file(cfg.root_dir.join(_ZERO_YML))
        self.secret = pkyaml.load_file(
            cfg.root_dir.join(_SECRET_SUBDIR).join(_ZERO_YML),
        )

    def host_db(self, channel, host):
        res = pkcollections.Dict(
            # Common defaults we allow overrides for
            host_run_d=pkio.py_path('/var/lib'),
            run_u='vagrant',
            root_u='root',
        )
        #TODO(robnagler) optimize by caching default and channels
        for l in _LEVELS:
            for x in self.base, self.secret:
                v = x[l]
                if l != 'default':
                    v = v.get(channel)
                    if not v:
                        continue
                    if l == 'host':
                        v = v.get(host)
                        if not v:
                            continue
                pkconfig.flatten_values(res, v)
        res.host = host.lower()
        res.channel = channel
        res.root_d = pkio.py_path(cfg.root_dir)
        res.secret_d = res.root_d.join(_SECRET_SUBDIR)
        res.srv_d = res.root_d.join(_SRV_SUBDIR)
        res.srv_host_d = res.srv_d.join(_HOST_SUBDIR)
        return res

    def channel_hosts(self):
        res = pkcollections.OrderedMapping()
        for c in pkconfig.VALID_CHANNELS:
            res[c] = sorted(
                self.base.host.get(c, pkcollections.Dict()).keys(),
            )
        return res


@pkconfig.parse_none
def _cfg_root(value):
    """Parse root directory"""
    #TODO(robnagler) encapsulate this sirepo.server is the same thing
    from pykern import pkio, pkinspect
    import os, sys

    if value:
        assert os.path.isabs(value), \
            '{}: must be absolute'.format(value)
        value = pkio.py_path(value)
        assert value.check(dir=1), \
            '{}: must be a directory and exist'.format(value)
    else:
        assert pkconfig.channel_in('dev'), \
            'must be configured except in DEV'
        fn = pkio.py_path(sys.modules[pkinspect.root_package(_cfg_root)].__file__)
        root = pkio.py_path(pkio.py_path(fn.dirname).dirname)
        # Check to see if we are in our ~/src/radiasoft/<pkg> dir. This is a hack,
        # but should be reliable.
        if not root.join('requirements.txt').check():
            # Don't run from an install directory
            root = pkio.py_path('.')
        value = root.join(_DEFAULT_DB_SUBDIR)
        if not value.check(dir=True):
            _setup_dev(value)
    return value


#TODO(robnagler) needs to moved
def _add_host(channel, host, passwd_file):
    import subprocess
    p = subprocess.Popen(
        ['openssl', 'passwd', '-stdin', '-apr1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    pw = _gen_password()
    out, err = p.communicate(input=pw)
    with open(passwd_file, 'a') as f:
        f.write('{}:{}\n'.format(host, out.rstrip()))
    return pw


def _gen_password():
    import random
    import string

    chars = string.ascii_lowercase + string.digits + string.ascii_uppercase
    return ''.join(random.choice(chars) for _ in range(32))


#TODO(robnagler) happen in a pkcli
def _setup_dev(root):
    from pykern import pkresource
    from pykern import pkio
    from pykern import pkjinja
    import re

    def _sym(old, new):
        assert old.check(), \
            '{}: does not exist'.format(old)
        new.mksymlinkto(old, absolute=False)

    srv = pkio.mkdir_parent(root.join(_SRV_SUBDIR))
    secret_d = pkio.mkdir_parent(root.join(_SECRET_SUBDIR))
    nginx_d = pkio.mkdir_parent(root.join(_NGINX_SUBDIR))
    j2_ctx = pkcollections.Dict(
        srv_d=str(srv),
        port=8000,
        host='v4.bivio.biz',
        channel='dev',
        master='v5.bivio.biz',
        passwd_file=str(secret_d.join('dev-nginx-passwd')),
    )
    j2_ctx.passwd = _add_host(j2_ctx.channel, j2_ctx.host, j2_ctx.passwd_file)
    _sym(
        pkio.py_path('~/src/radiasoft/download/bin/install.sh'),
        srv.join('index.html'),
    )
    _sym(
        pkio.py_path(pkresource.filename('rsconf.sh')),
        srv.join('rsconf.sh'),
    )
    dev_root = pkio.py_path(pkresource.filename('dev'))
    for f in pkio.walk_tree(dev_root):
        # TODO(robnagler) ignore backup files
        if str(f).endswith('~') or str(f).startswith('#'):
            continue
        x = f.relto(dev_root)
        dst = root.join(re.sub('.jinja$', '', x))
        pkio.mkdir_parent_only(dst)
        pkjinja.render_file(f, j2_ctx, output=dst, strict_undefined=True)


cfg = pkconfig.init(
    root_dir=(None, _cfg_root, 'Top of rsonf tree'),
)
