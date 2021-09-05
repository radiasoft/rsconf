# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcompat
from pykern import pkio
from pykern import pkjson
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
import base64
import bcrypt


_DOCKER_HUB_HOST = 'docker.io'
REGISTRY_IMAGE = _DOCKER_HUB_HOST + '/library/registry:2'

_DB_SUBDIR = 'db'
_TLS_BASE = 'docker_registry'
_CERTS_D = pkio.py_path('/etc/docker/certs.d')
_CA_TRUST_D = pkio.py_path('/etc/pki/ca-trust/source/anchors')
_GLOBAL_CONF = '/etc/docker/registry/config.yml'
_PASSWD_SECRET_JSON_F = 'docker_registry_passwd.json'
_PASSWD_SECRET_F = 'docker_registry_passwd'
_HTTP_SECRET_F = 'docker_registry_http_secret'
_PASSWD_VISIBILITY = 'global'
_HTTP_SECRET_VISIBILITY = _PASSWD_VISIBILITY
# 5000 is hardwired, because Docker doesn't have a way of configuring it; they
# just assume you are using the docker proxy (-P 80:5000) or a regular proxy (which
# doesn't work so well). Only when we open up iptables, will we need to share this
# via some call.
_PORT = 5000

#TODO(robnagler) how to clean registry?

#TODO(robnagler) need to proxy registry to control access to push (WTF???)
# http://mindtrove.info/control-read-write-access-docker-private-registry/

def absolute_image(*args, **kwargs):
    j, i, l = _image_args(*args, **kwargs)
    if not ':' in i:
        i += f':{j.rsconf_db.channel}'
    if l:
        return i
    h = _DOCKER_HUB_HOST
    if update_j2_ctx(j):
        h = j.docker_registry.http_addr
    if i.startswith(_DOCKER_HUB_HOST) or i.startswith(h):
        return i
    return f'{h}/{i}'


def host_init(hdb, host):
    jf = db.secret_path(hdb, _PASSWD_SECRET_JSON_F, visibility=_PASSWD_VISIBILITY)
    if jf.check():
        with jf.open() as f:
            y = pkjson.load_any(f)
    else:
        y = PKDict()
    assert not host in y, \
        '{}: host already exists'.format(host)
    y[host] = db.random_string()
    pkjson.dump_pretty(y, filename=jf)
    pf = db.secret_path(hdb, _PASSWD_SECRET_F, visibility=_PASSWD_VISIBILITY)
    with pf.open(mode='at') as f:
        f.write(
            '{}:{}\n'.format(
                host,
                pkcompat.from_bytes(
                    bcrypt.hashpw(
                        pkcompat.to_bytes(y[host]),
                        bcrypt.gensalt(5),
                    ),
                ),
            ),
        )


def image_is_local(*args, **kwargs):
    return _image_args(*args, *kwargs)[2]


def install_crt_and_login(compt, j2_ctx):
    from rsconf.pkcli import tls

    if not update_j2_ctx(j2_ctx):
        return
    jf = db.secret_path(j2_ctx, _PASSWD_SECRET_JSON_F, visibility=_PASSWD_VISIBILITY)
    with jf.open() as f:
        y = pkjson.load_any(jf)
    u = j2_ctx.rsconf_db.host
    p = y.get(u, None)
    if not p:
        return
    j2_ctx.docker.auths[j2_ctx.docker_registry.http_addr] = dict(
        auth=pkcompat.from_bytes(
            base64.b64encode(pkcompat.to_bytes(u + ':' + pkcompat.from_bytes(p))),
        ),
    )
    compt.install_access(mode='700', owner=j2_ctx.docker_registry.run_u)
    crt = component.tls_key_and_crt(j2_ctx, j2_ctx.docker_registry.host).crt
    if not tls.is_self_signed_crt(crt):
        return
    compt.install_directory(_CERTS_D)
    d = _CERTS_D.join(j2_ctx.docker_registry.http_addr)
    compt.install_directory(d)
    compt.install_access(mode='400', owner=j2_ctx.docker_registry.run_u)
    compt.install_abspath(crt, d.join('ca.crt'))
    # need in /etc/pki as well (now)
    # https://success.docker.com/article/i-get-x509-certificate-signed-by-unknown-authority-error-when-i-try-to-login-to-my-dtr-with-default-certificates
    compt.install_abspath(crt, _CA_TRUST_D.join(j2_ctx.docker_registry.host + '.crt'))
    compt.append_root_bash('update-ca-trust')


def update_j2_ctx(j2_ctx):
    #TODO(robnagler) exit if already initialzed.
    if not j2_ctx.docker_registry.host:
        return False
    addr = '{}:{}'.format(j2_ctx.docker_registry.host, _PORT)
    j2_ctx.docker_registry.update(PKDict(
        http_addr=addr,
        http_host='https://' + addr,
        run_u=j2_ctx.rsconf_db.root_u,
    ))
    return True


class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        # https://docs.docker.com/registry/configuration/
        self.buildt.require_component('docker')
        j2_ctx = self.hdb.j2_ctx_copy()
        run_d = systemd.docker_unit_prepare(self, j2_ctx)
        assert update_j2_ctx(j2_ctx), \
            'no registry host'
        conf_f = run_d.join('config.yml')
        volumes = [
            [conf_f, _GLOBAL_CONF],
        ]
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            # Specify pull from docker.io directly to avoid registry not yet running
            image=REGISTRY_IMAGE,
            cmd=None,
            after=['docker.service'],
            run_u=j2_ctx.docker_registry.run_u,
            volumes=volumes,
        )
        kc = self.install_tls_key_and_crt(j2_ctx.docker_registry.host, run_d)
        db_d = run_d.join(_DB_SUBDIR)
        j2_ctx.docker_registry.update(
            auth_htpasswd_path=run_d.join('passwd'),
            conf_f=conf_f,
            db_d=db_d,
            http_tls_certificate=kc.crt,
            http_tls_key=kc.key,
        )
        j2_ctx.docker_registry.http_secret = self.secret_path_value(
            _HTTP_SECRET_F,
            lambda: db.random_string(length=64),
            visibility=_HTTP_SECRET_VISIBILITY,
        )[0]
        self.install_secret_path(
            _PASSWD_SECRET_F,
            j2_ctx.docker_registry.auth_htpasswd_path,
            gen_secret=db.random_string,
            visibility=_PASSWD_VISIBILITY,
        )
        self.install_access(mode='700', owner=j2_ctx.docker_registry.run_u)
        self.install_directory(db_d)
        self.install_access(mode='400', owner=j2_ctx.docker_registry.run_u)
        self.install_resource(
            'docker_registry/config.yml', j2_ctx, j2_ctx.docker_registry.conf_f)
        self.rsconf_service_restart()


def _image_args(compt, j2_ctx=None, image=None, image_is_local=None):
    if j2_ctx is None:
        j2_ctx = compt.j2_ctx
    if not image:
        image = j2_ctx[compt.name].docker_image
    if image_is_local is None:
        image_is_local = j2_ctx.pkunchecked_nested_get(
            f'{compt.name}.docker_image_is_local',
        )
    return (j2_ctx, image, bool(image_is_local))
