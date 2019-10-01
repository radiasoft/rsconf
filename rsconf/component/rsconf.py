# -*- coding: utf-8 -*-
u"""rsconf server config

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkjson
from rsconf import component
import urlparse


_PASSWD_SECRET_JSON_F = 'rsconf_auth.json'
PASSWD_SECRET_F = 'rsconf_auth'


class T(component.T):

    def internal_build_compile(self):
        from rsconf.component import nginx
        from rsconf import db

        # docker is required to build container-perl
        self.buildt.require_component('docker', 'nginx')
        self.j2_ctx = self.hdb.j2_ctx_copy()
        jc = self.j2_ctx
        jc.rsconf = pkcollections.Dict(
            auth_f=nginx.CONF_D.join(PASSWD_SECRET_F),
            srv_d=jc.rsconf_db.srv_d,
            host_subdir=db.HOST_SUBDIR,
        )

    def internal_build_write(self):
        from rsconf.component import nginx
        from rsconf import db

        jc = self.j2_ctx
        nginx.install_vhost(
            self,
            vhost=_vhost(jc),
            j2_ctx=jc,
        )
        nginx.install_auth(
            self,
            PASSWD_SECRET_F,
            jc.rsconf.auth_f,
            db.VISIBILITY_GLOBAL,
            jc,
        )


def host_init(j2_ctx, host):
    from rsconf import db
    import urlparse

    jf = db.secret_path(j2_ctx, _PASSWD_SECRET_JSON_F, visibility=db.VISIBILITY_GLOBAL)
    if jf.check():
        with jf.open() as f:
            y = pkjson.load_any(f)
    else:
        y = pkcollections.Dict()
    if not host in y:
        y[host] = _passwd_entry(j2_ctx, host)
        pkjson.dump_pretty(y, filename=jf)
    return """install -m 600 /dev/stdin /root/.netrc <<'EOF'
machine {} login {} password {}
EOF
curl {} | install_server={} bash -s {}
# On {}: ssh {} true""".format(
        _vhost(j2_ctx),
        host,
        y[host],
        j2_ctx.rsconf_db.http_host,
        j2_ctx.rsconf_db.http_host,
        host,
        j2_ctx.bkp.primary,
        host,
    )


def passwd_secret_f(j2_ctx):
    from rsconf import db

    return db.secret_path(j2_ctx, PASSWD_SECRET_F, visibility=db.VISIBILITY_GLOBAL)


def _passwd_entry(j2_ctx, host):
    from rsconf import db
    import subprocess

    pw = db.random_string()
    pf = passwd_secret_f(j2_ctx)
    p = subprocess.Popen(
        ['openssl', 'passwd', '-stdin', '-apr1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    out, err = p.communicate(input=pw)
    with pf.open(mode='a') as f:
        f.write('{}:{}\n'.format(host, out.rstrip()))
    return pw


def _vhost(j2_ctx):
    u = urlparse.urlparse(j2_ctx.rsconf_db.http_host)
    return u.hostname
