# -*- coding: utf-8 -*-
u"""create docker configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkcompat
from pykern import pkio
from pykern.pkdebug import pkdp
from rsconf import component

DOCKER_SOCK = '/var/run/docker.sock'

_CONF_DIR = pkio.py_path('/etc/docker')
_TLS_DIR = _CONF_DIR.join('tls')
_DAEMON_JSON = _CONF_DIR.join('daemon.json')
_DAEMON_PORT = 2376
_ROOT_CONFIG_JSON = pkio.py_path('/root/.docker/config.json')
_TLS_BASENAME = 'docker_tls'
_TLS_CA_BASENAME = _TLS_BASENAME + '_ca'


class T(component.T):
    def internal_build(self):
        from rsconf.component import docker_registry
        from rsconf.component import docker_cache
        from rsconf.component import db_bkp
        from rsconf import systemd

        self.buildt.require_component('base_all', 'db_bkp')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.docker
        systemd.unit_prepare(self, j2_ctx, [_CONF_DIR, ])
        z.run_d = systemd.unit_run_d(j2_ctx, 'docker')
        z.data_d = z.run_d
        z.run_u = j2_ctx.rsconf_db.root_u
        docker_registry.update_j2_ctx(j2_ctx)
        docker_cache.update_j2_ctx(j2_ctx)
        z.daemon_hosts = ["unix://"]
        self.install_access(mode='700', owner=z.run_u)
        self.install_directory(_CONF_DIR)
        if z.setdefault('tls_host', j2_ctx.rsconf_db.host):
            self._setup_tls_host(j2_ctx, z)
        self.install_access(mode='400')
        self.install_resource(
            'docker/daemon.json',
            j2_ctx,
            _DAEMON_JSON,
        )
        self.append_root_bash_with_main(j2_ctx)
        j2_ctx.docker.setdefault('auths', pkcollections.Dict())
        # Must be after everything else related to daemon
        docker_registry.install_crt_and_login(self, j2_ctx)
        docker_cache.install_crt(self, j2_ctx)
        j2_ctx.docker.config_login = dict(
            detachKeys='ctrl-],q',
        )
        if j2_ctx.docker.auths:
            j2_ctx.docker.config_login['auths'] = _dict(j2_ctx.docker.auths)
        self.install_access(mode='700', owner=z.run_u)
        self.install_directory(_ROOT_CONFIG_JSON.dirname)
        self.install_access(mode='400')
        self.install_resource(
            'docker/root_config.json',
            j2_ctx,
            _ROOT_CONFIG_JSON,
        )
        systemd.install_unit_override(self, j2_ctx)
        systemd.unit_enable(self, j2_ctx)
        self.rsconf_service_restart()
        db_bkp.install_script_and_subdir(
            self,
            j2_ctx,
            run_u=z.run_u,
            run_d=z.run_d,
        )

    def _setup_tls_host(self, j2_ctx, z):
        import socket
        import ipaddress

        c, ca = _self_signed_crt(j2_ctx, j2_ctx.rsconf_db.host)
        self.install_access(mode='700', owner=z.run_u)
        self.install_directory(_TLS_DIR)
        self.install_access(mode='400', owner=z.run_u)
        z.tls = pkcollections.Dict()
        # just to match docker's documentation, not really important
        for k, b in ('crt', 'cert'), ('key', 'key'):
            z.tls[k] = _TLS_DIR.join(b + '.pem')
            self.install_abspath(c[k], z.tls[k])
        z.tls.ca_crt = _TLS_DIR.join('cacert.pem')
        self.install_abspath(ca['crt'], z.tls.ca_crt)
        z.tls.ip = socket.gethostbyname(z.tls_host)
        assert ipaddress.ip_address(pkcompat.locale_str(z.tls.ip)).is_private, \
            'tls_host={} is on public ip={}'.format(z.tls_host, z.tls.ip)
        z.daemon_hosts.append('tcp://{}:{}'.format(z.tls.ip, _DAEMON_PORT))


def setup_cluster(compt, hosts, tls_d, run_u, j2_ctx):
    from rsconf import db

    compt.install_access(mode='700', owner=run_u)
    compt.install_directory(tls_d)
    b = db.secret_path(j2_ctx, compt.name + '_' + _TLS_BASENAME, visibility='host')
    pkio.mkdir_parent_only(b)
    for h in hosts:
        c, ca = _self_signed_crt(j2_ctx, h)
        c = _signed_crt(j2_ctx, ca, b.join(h))
        d = tls_d.join(h)
        compt.install_access(mode='700')
        compt.install_directory(d)
        compt.install_access(mode='400')
        # POSIT: sirepo.runner.docker uses {cacert,cert,key}.pem
        compt.install_abspath(ca.crt, d.join('cacert.pem'))
        compt.install_abspath(c.crt, d.join('cert.pem'))
        compt.install_abspath(c.key, d.join('key.pem'))


def _crt_create(basename, op):
    from rsconf.pkcli import tls

    res = pkcollections.Dict(
        key=basename + tls.KEY_EXT,
        crt=basename + tls.CRT_EXT,
    )
    if res.crt.check():
        return res
    pkio.mkdir_parent_only(res.crt)
    return op()


def _dict(value):
    # may be pkcollections.Dict which is subclass of dict
    if not isinstance(value, dict):
        return value
    res = {}
    for k, v in value.items():
        res[k] = _dict(v)
    return res


def _self_signed_crt(j2_ctx, host):
    from rsconf.pkcli import tls
    from rsconf import db

    b = db.secret_path(
        j2_ctx,
        _TLS_CA_BASENAME,
        visibility='host',
        qualifier=host,
    )
    ca = _crt_create(
        b,
        # certificate cannot match host so we just create an arbitrary name
        lambda: tls.gen_ca_crt('root-ca.' + host, basename=str(b)),
    )
    b = db.secret_path(
        j2_ctx,
        _TLS_BASENAME,
        visibility='host',
        qualifier=host,
    )
    c = _crt_create(
        b,
        lambda: tls.gen_signed_crt(ca.key, str(b), host),
    )
    return c, ca


def _signed_crt(j2_ctx, ca, basename):
    from rsconf.pkcli import tls

    #TODO(robnagler) if the ca changes, then need to recreate the crt
    return _crt_create(
        basename,
        lambda: tls.gen_signed_crt(ca.key, basename, j2_ctx.rsconf_db.host),
    )
