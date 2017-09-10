# -*- coding: utf-8 -*-
u"""Database

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig


_SRV_SUBDIR = 'srv'
_DEFAULT_DB_SUBDIR = 'run'
_SECRET_SUBDIR = 'secret'

class T(pkcollections.Dict):

    def __init__(self, *args, **kwargs):
        from pykern import pkyaml

        super(T, self).__init__(*args, **kwargs)
        self.zdb = pkyaml.load_file(cfg.root.join('000.yml'))
        self.root = cfg.root
        self.srv = self.root(_SRV_SUBDIR)
        self.guest_run_d = pkio.py_path('/var/lib')
        self.guest_user = 'vagrant'
        self.root_user = 'root'


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
    pkio.mkdir_parent(root.join(_SECRET_SUBDIR))
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
