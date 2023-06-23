# -*- coding: utf-8 -*-
"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern import pkio
from pykern import pkjson
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
import base64
import bcrypt


_GLOBAL_CONF = "/etc/docker/registry/config.yml"
_DB_SUBDIR = "db"
# 5000 is hardwired, because Docker doesn't have a way of configuring it; they
# just assume you are using the docker proxy (-P 80:5000) or a regular proxy (which
# doesn't work so well). Only when we open up iptables, will we need to share this
# via some call.
_PORT = 5000
_CERTS_D = pkio.py_path("/etc/docker/certs.d")


def install_crt(compt, j2_ctx):
    if not update_j2_ctx(j2_ctx):
        return
    if not j2_ctx.component.tls_crt_create:
        # not self-signed so don't need to install the cert
        return
    # https://docs.docker.com/registry/insecure/#use-self-signed-certificates
    compt.install_access(mode="700", owner=j2_ctx.docker.run_u)
    z = j2_ctx.docker_cache
    compt.install_directory(_CERTS_D)
    d = _CERTS_D.join(z.http_addr)
    compt.install_directory(d)
    crt = component.tls_key_and_crt(j2_ctx, z.host).crt
    compt.install_access(mode="400")
    compt.install_abspath(crt, d.join("ca.crt"))


def update_j2_ctx(j2_ctx):
    from rsconf.component import docker_registry

    h = j2_ctx.pkunchecked_nested_get("docker_cache.host", "")
    if h == "":
        return False
    if docker_registry.update_j2_ctx(j2_ctx):
        raise AssertionError(
            f"docker_registry.host={j2_ctx.docker_registry.host} and docker_cache.host={h} cannot both be defined",
        )
    addr = "{}:{}".format(h, _PORT)
    j2_ctx.docker_cache.update(
        PKDict(
            http_addr=addr,
            http_host="https://" + addr,
        )
    )
    return True


class T(component.T):
    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        # https://docs.docker.com/registry/configuration/
        self.buildt.require_component("docker")
        j2_ctx = self.hdb.j2_ctx_copy()
        assert update_j2_ctx(j2_ctx), "no docker_cache.host in hdb"
        z = j2_ctx.docker_cache
        z.run_d = systemd.docker_unit_prepare(self, j2_ctx)
        # Has to run as root, because 3rd party container
        z.run_u = j2_ctx.rsconf_db.root_u
        z.conf_f = z.run_d.join("config.yml")
        z.db_d = z.run_d.join(_DB_SUBDIR)
        volumes = [
            [z.conf_f, _GLOBAL_CONF],
        ]
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            image=docker_registry.REGISTRY_IMAGE,
            after=["docker.service"],
            run_u=z.run_u,
            volumes=volumes,
        )
        kc = self.install_tls_key_and_crt(z.host, z.run_d)
        z.update(
            http_tls_certificate=kc.crt,
            http_tls_key=kc.key,
        )
        self.install_access(mode="700", owner=z.run_u)
        self.install_directory(z.db_d)
        self.install_access(mode="400", owner=z.run_u)
        self.install_resource("docker_cache/config.yml", j2_ctx, z.conf_f)
        self.rsconf_service_restart()
