# -*- coding: utf-8 -*-
u"""Test tree

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio
from pykern import pkjinja
from pykern import pkresource
from pykern.pkdebug import pkdp
from rsconf import db
import grp
import os
import pwd
import re
import subprocess

NGINX_SUBDIR = 'nginx'

def default_command():
    from rsconf.component import rsconf

    root_d = db.cfg.root_d
    if root_d.check():
        return '{}: already exists'.format(root_d)
    srv = pkio.mkdir_parent(root_d.join(db.SRV_SUBDIR))

    def _sym(old, new_base=None):
        old = pkio.py_path(old)
        if not new_base:
            new_base = old.basename
        assert old.check(), \
            '{}: does not exist'.format(old)
        srv.join(new_base).mksymlinkto(old, absolute=False)

    # ssh-keygen -q -N '' -C rsconf -t rsa -b 4096 -f /var/tmp/foo
    # -- don't need this
    db_d = pkio.mkdir_parent(root_d.join(db.DB_SUBDIR))
    secret_d = pkio.mkdir_parent(db_d.join(db.SECRET_SUBDIR))
    nginx_d = pkio.mkdir_parent(root_d.join(NGINX_SUBDIR))
    boot_hdb = pkcollections.Dict(rsconf_db=pkcollections.Dict(
        secret_d=secret_d,
        channel='dev',
    ))
    j2_ctx = pkcollections.Dict(
        srv_d=str(srv),
        uid=os.getuid(),
        user=pwd.getpwuid(os.getuid())[0],
        group=grp.getgrgid(os.getgid())[0],
        host='v4.radia.run',
        all_host='v5.radia.run',
        master='v3.radia.run',
        port=2916,
    )
    # bootstrap
    j2_ctx.update(boot_hdb)
    j2_ctx.rsconf_db.http_host = 'http://{}:{}'.format(j2_ctx.master, j2_ctx.port)
    j2_ctx.bkp = pkcollections.Dict(primary=j2_ctx.master)
    j2_ctx.passwd_f = rsconf.passwd_secret_f(j2_ctx)
    for h in j2_ctx.host, j2_ctx.master, j2_ctx.all_host:
        _add_host(j2_ctx, srv, h)
    _sym('~/src/radiasoft/download/bin/install.sh', 'index.html')
    _sym(pkresource.filename('rsconf/rsconf.sh'), 'rsconf.sh')
    dev_d = pkio.py_path(pkresource.filename('dev'))
    for f in pkio.walk_tree(dev_d):
        # TODO(robnagler) ignore backup files
        if str(f).endswith('~') or str(f).startswith('#'):
            continue
        x = f.relto(dev_d)
        dst = root_d.join(re.sub('.jinja$', '', x))
        pkio.mkdir_parent_only(dst)
        pkjinja.render_file(f, j2_ctx, output=dst, strict_undefined=True)
    rpm_d = pkio.py_path(root_d.dirname).join('rpm')
    pkio.mkdir_parent(rpm_d)
    root_d.join('rpm').mksymlinkto(rpm_d, absolute=False)
    subprocess.check_call(['bash', str(secret_d.join('setup_dev.sh'))])
    # dev only, really insecure, but makes consistent builds easy
    _sym('~/src/radiasoft')
    _sym('~/src/biviosoftware')
    # Tests init_docker_registry, which should only be set for specific hosts
    subprocess.check_call(['rsconf', 'host', 'init_docker_registry', j2_ctx.host])


#TODO(robnagler) needs to moved
def _add_host(j2_ctx, srv, host):
    from rsconf.component import docker_registry
    from rsconf.component import rsconf

    netrc = rsconf.host_init(j2_ctx, host)
    pkio.write_text(srv.join(host + '-netrc'), netrc)
    if host == j2_ctx.master:
        docker_registry.host_init(j2_ctx, host)
