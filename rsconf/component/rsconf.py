# -*- coding: utf-8 -*-
"""rsconf server config

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from pykern import pkcompat
from pykern import pkjson
from pykern.pkdebug import pkdp
from rsconf import component
from urllib.parse import urlparse

_PASSWD_SECRET_JSON_F = "rsconf_auth.json"
PASSWD_SECRET_F = "rsconf_auth"


class T(component.T):
    def internal_build_compile(self):
        from rsconf.component import nginx
        from rsconf import db

        # docker is required to build container-perl
        self.buildt.require_component("docker", "nginx")
        self.j2_ctx = self.hdb.j2_ctx_copy()
        jc = self.j2_ctx
        jc.rsconf = PKDict(
            auth_f=nginx.CONF_D.join(PASSWD_SECRET_F),
            srv_d=jc.rsconf_db.srv_d,
            host_subdir=jc.rsconf_db.srv_host_d.basename,
        )

    def internal_build_write(self):
        from rsconf.component import nginx
        from rsconf import db

        jc = self.j2_ctx

        f, h = _vhost(jc)
        if f:
            self.append_root_bash(": nothing to do")
            return
        nginx.install_vhost(
            self,
            vhost=h,
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

    s, h = _vhost(j2_ctx)
    jf = db.secret_path(j2_ctx, _PASSWD_SECRET_JSON_F, visibility=db.VISIBILITY_GLOBAL)
    if jf.check():
        with jf.open() as f:
            y = pkjson.load_any(f)
    else:
        y = PKDict()
    if not host in y:
        y[host] = _passwd_entry(j2_ctx, host)
        pkjson.dump_pretty(y, filename=jf)
    c = f'curl {j2_ctx.rsconf_db.http_host + "/index.sh" if s else ""} | install_server={j2_ctx.rsconf_db.http_host} bash -s {host}'
    if s:
        return f"""Bootstrapping build server
Run:
{c}
Then update http_host in db/000.yml and run host init again"""
    return f"""install -m 600 /dev/stdin /root/.netrc <<'EOF'
machine {h} login {host} password {y[host]}
EOF
{c}
# On {j2_ctx.bkp.primary}: ssh {host} true"""


def passwd_secret_f(j2_ctx):
    from rsconf import db

    return db.secret_path(j2_ctx, PASSWD_SECRET_F, visibility=db.VISIBILITY_GLOBAL)


def _passwd_entry(j2_ctx, host):
    from rsconf import db
    import subprocess

    pw = db.random_string()
    pf = passwd_secret_f(j2_ctx)
    p = subprocess.Popen(
        ["openssl", "passwd", "-stdin", "-apr1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    out, err = p.communicate(input=pkcompat.to_bytes(pw))
    with pf.open(mode="at") as f:
        f.write("{}:{}\n".format(host, pkcompat.from_bytes(out).rstrip()))
    return pw


def _vhost(j2_ctx):
    u = urlparse(j2_ctx.rsconf_db.http_host)
    return u.scheme == "file", u.hostname
