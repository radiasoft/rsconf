# -*- coding: utf-8 -*-
u"""Database

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio


_ZERO_YML = '000.yml'
_SRV_SUBDIR = 'srv'
_DEFAULT_DB_SUBDIR = 'run'
_SECRET_SUBDIR = 'secret'
_LEVELS = ('default', 'channel', 'host')

class T(pkcollections.Dict):

    def __init__(self, *args, **kwargs):
        from pykern import pkyaml

        super(T, self).__init__(*args, **kwargs)
        self.base = pkyaml.load_file(cfg.root_d.join(_ZERO_YML))
        self.secret = pkyaml.load_file(
            cfg.root.join(_SECRET_SUBDIR)).join(_ZERO_YML))

    def host_db(self, host):
        channel = self.base.host[host].channel
        res = pkcollections.Dict(
            # Common defaults we allow overrides for
            guest_run_d=pkio.py_path('/var/lib'),
            guest_u='vagrant',
            root_u='root',
        )
        #TODO(robnagler) optimize by caching default and channels
        for l in levels:
            for x in self.base, self.secret:
                v = x[l]
                if l == 'host':
                    v = x[host]
                elif l == 'channel':
                    v = v['channel']
                pkconfig.flatten_values(res, v)
        # Can't override th
        res.host = host.lower()
        res.channel = channel
        res.dst_d = res.srv_d.join(res.host)
        res.root_d = pkio.py_path(cfg.root)
        res.secret_d = res.root_d.join(_SECRET_SUBDIR)
        res.srv_d = res.root_d.join(_SRV_SUBDIR)
        return res

    def host_list(self):
        res = []
        for c in pkconfig.VALID_CHANNELS:
            res.extend(
                sorted(
                    self.base.host.get(c, pkcollections.Dict()).keys(),
                ),
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
        assert value.ensure(dir=1), \
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


def _setup_dev(root):
    from pykern import pkresource
    from pykern import pkio

    def _sym(old, new):
        assert old.check(), \
            '{}: does not exist'.format(old)
        new.mksymlinkto(old, absolute=False)

    srv = pkio.mkdir_parent(root.join(_SRV_SUBDIR))
    #TODO(robnagler) be more discriminating with ~/src/radiasoft/download
    for f in 'radiasoft', 'biviosoftware':
        _sym(pkio.py_path('~/src').join(f), srv.join(f))
    _sym(pkio.py_path('~/src/radiasoft/download/bin/index.sh'), srv.join('index.html'))
    dev_root = pkio.py_path(pkresource.filename('dev'))
    for f in pkio.walk_tree(dev_root):
        # TODO(robnagler) ignore backup files
        if str(f).endswith('~') or str(f).startswith('#'):
            continue
        dst = root.join(f.relto(dev_root))
        pkio.mkdir_parent_only(dst)
        _sym(f, dst)


cfg = pkconfig.init(
    root=(None, _cfg_root, 'Top of rsonf tree'),
)
