"""Test tree

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern import pkcollections
from pykern import pkio
from pykern import pkjinja
from pykern import pkresource
from pykern import pkunit
from pykern.pkdebug import pkdp
from rsconf import db
import grp
import os
import pwd
import re
import subprocess

NGINX_SUBDIR = "nginx"


def default_command():
    import rsconf.component
    import rsconf.component.rsconf
    import rsconf.pkcli.tls

    root_d = db.root_d()
    if (
        root_d.check()
        and not pkunit.is_test_run()
        and db.cfg.root_d != db.UNIT_TEST_ROOT_D
    ):
        return f"{root_d}: already exists"
    srv = pkio.mkdir_parent(root_d.join(db.SRV_SUBDIR))

    def _sym(old, new_base=None):
        old = pkio.py_path(old)
        if not new_base:
            new_base = old.basename
        assert old.check(), "{}: does not exist".format(old)
        srv.join(new_base).mksymlinkto(old, absolute=False)

    # ssh-keygen -q -N '' -C rsconf -t rsa -b 4096 -f /var/tmp/foo
    # -- don't need this
    db_d = pkio.mkdir_parent(root_d.join(db.DB_SUBDIR))
    secret_d = pkio.mkdir_parent(db_d.join(db.SECRET_SUBDIR))
    nginx_d = pkio.mkdir_parent(root_d.join(NGINX_SUBDIR))
    boot_hdb = pkcollections.Dict(
        rsconf_db=pkcollections.Dict(
            secret_d=secret_d,
            channel="dev",
        )
    )
    j2_ctx = pkcollections.Dict(
        all_host="v9.radia.run",
        group=grp.getgrgid(os.getgid())[0],
        host="v4.radia.run",
        master="v3.radia.run",
        port=2916,
        root_d=root_d,
        srv_d=str(srv),
        uid=os.getuid(),
        user=pwd.getpwuid(os.getuid())[0],
        worker5_host="v5.radia.run",
        worker6_host="v6.radia.run",
    )
    hosts = [h for h in j2_ctx.values() if str(h).endswith(".radia.run")]
    # bootstrap
    j2_ctx.update(boot_hdb)
    j2_ctx.rsconf_db.http_host = "http://{}:{}".format(j2_ctx.master, j2_ctx.port)
    j2_ctx.bkp = pkcollections.Dict(primary=j2_ctx.host)
    j2_ctx.passwd_f = rsconf.component.rsconf.passwd_secret_f(j2_ctx)
    for h in hosts:
        _add_host(j2_ctx, srv, h)
    _sym("~/src/radiasoft/download/bin/install.sh", "index.html")
    _sym("~/src/radiasoft/download/bin/install.sh", "index.sh")
    _sym(pkresource.filename("rsconf/rsconf.sh"), "rsconf.sh")
    dev_d = pkio.py_path(pkresource.filename("dev"))
    for f in pkio.walk_tree(dev_d):
        x = str(f.relto(dev_d))
        if not ("local/" in x and x.endswith(".sh.jinja")):
            x = re.sub(".jinja$", "", x)
        dst = root_d.join(x)
        pkio.mkdir_parent_only(dst)
        if f.basename == dst.basename:
            f.copy(dst)
        else:
            pkjinja.render_file(f, j2_ctx, output=dst, strict_undefined=True)
    n = []
    for e in "rpm", "proprietary":
        d = pkio.py_path(root_d.dirname).join(e)
        pkio.mkdir_parent(d)
        root_d.join(e).mksymlinkto(d, absolute=False)
        n.append(str(d))
    subprocess.check_call(
        ["bash", str(secret_d.join("setup_dev.sh")), *n],
    )
    # dev only, really insecure, but makes consistent builds easy
    _sym("~/src/radiasoft")
    _sym("~/src/biviosoftware")
    for h in hosts:
        # needed to be able to talk setup certs for registry so we can
        # pull private images from all hosts. Only used in dev, because
        # private registry doesn't protect against pushes from these hosts.
        if h != j2_ctx.master:
            subprocess.check_call(["rsconf", "host", "init_docker_registry", h])
    tls_d = secret_d.join(rsconf.component.TLS_SECRET_SUBDIR)
    tls_d.ensure(dir=True)
    for h in (
        "jupyter." + j2_ctx.all_host,
        "jupyter." + j2_ctx.host,
        j2_ctx.all_host,
        j2_ctx.master,
        j2_ctx.worker5_host,
        j2_ctx.worker6_host,
    ):
        rsconf.pkcli.tls.gen_self_signed_crt(
            tls_d.join(h),
            h,
        )
    rsconf.pkcli.tls.gen_self_signed_crt(
        tls_d.join("star." + j2_ctx.host),
        "*." + j2_ctx.host,
        j2_ctx.host,
    )


# TODO(robnagler) needs to moved
def _add_host(j2_ctx, srv, host):
    from rsconf.component import docker_registry
    from rsconf.component import rsconf

    netrc = rsconf.host_init(j2_ctx, host)
    pkio.write_text(srv.join(host + "-netrc"), netrc)
    if host == j2_ctx.master:
        docker_registry.host_init(j2_ctx, host)
