# -*- coding: utf-8 -*-
u"""Test tree

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

NGINX_SUBDIR = 'nginx'

def default_command():
    from pykern import pkio
    from pykern import pkcollections
    from pykern import pkjinja
    from pykern import pkresource
    from rsconf import db
    import re

    root = db.cfg.root_dir
    if root.check():
        return '{}: already exists'.format(root)
    srv = pkio.mkdir_parent(root.join(db.SRV_SUBDIR))

    def _sym(old, new_base=None):
        old = pkio.py_path(old)
        if not new_base:
            new_base = old.basename
        assert old.check(), \
            '{}: does not exist'.format(old)
        srv.join(new_base).mksymlinkto(old, absolute=False)

    # ssh-keygen -q -N '' -C rsconf -t rsa -b 4096 -f /var/tmp/foo
    # -- don't need this
    secret_d = pkio.mkdir_parent(root.join(db.SECRET_SUBDIR))
    nginx_d = pkio.mkdir_parent(root.join(NGINX_SUBDIR))
    boot_hdb = pkcollections.Dict(rsconf_db_secret_d=secret_d, rsconf_db_channel='dev')
    j2_ctx = pkcollections.Dict(
        srv_d=str(srv),
        host='v4.radia.run',
        master='v5.radia.run',
        # You can't change this
        passwd_file=db.secret_path(boot_hdb, 'nginx-passwd', visibility='channel')
    )
    j2_ctx.update(boot_hdb)
    pw = {}
    for h in j2_ctx.host, j2_ctx.master:
        pw[h] = _add_host(j2_ctx, 'dev', h, j2_ctx.passwd_file)
    _sym('~/src/radiasoft/download/bin/install.sh', 'index.html')
    _sym(pkresource.filename('rsconf.sh'), 'rsconf.sh')
    dev_root = pkio.py_path(pkresource.filename('dev'))
    for f in pkio.walk_tree(dev_root):
        # TODO(robnagler) ignore backup files
        if str(f).endswith('~') or str(f).startswith('#'):
            continue
        x = f.relto(dev_root)
        dst = root.join(re.sub('.jinja$', '', x))
        pkio.mkdir_parent_only(dst)
        if not dst.basename.startswith('host-'):
            pkjinja.render_file(f, j2_ctx, output=dst, strict_undefined=True)
            continue
        for h, p in pw.iteritems():
            d = pkio.py_path(dst.dirname).join(dst.basename.replace('host', h))
            j2_ctx.passwd = p
            j2_ctx.host = h
            pkjinja.render_file(f, j2_ctx, output=d, strict_undefined=True)
            _sym(d)

    # dev only, really insecure, but makes consistent builds easy
    _sym('~/src/radiasoft')
    _sym('~/src/biviosoftware')


#TODO(robnagler) needs to moved
def _add_host(j2_ctx, channel, host, passwd_file):
    from rsconf.component import docker_registry
    from rsconf import db
    import subprocess

    p = subprocess.Popen(
        ['openssl', 'passwd', '-stdin', '-apr1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    pw = db.random_string()
    out, err = p.communicate(input=pw)
    with open(str(passwd_file), 'a') as f:
        f.write('{}:{}\n'.format(host, out.rstrip()))
    docker_registry.add_host(j2_ctx, host)
    return pw
