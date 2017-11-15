# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio
from pykern import pkyaml
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
import base64
import bcrypt
import yaml


_DB_SUBDIR = 'db'
_TLS_BASE = 'docker_registry'
_CERTS_D = pkio.py_path('/etc/docker/certs.d')
_GLOBAL_CONF = '/etc/docker/registry/config.yml'
_ROOT_CONFIG_JSON = pkio.py_path('/root/.docker/config.json')
_DOCKER_HUB_HOST = 'docker.io'
_PASSWD_SECRET_YAML_F = 'docker_registry_passwd.yml'
_PASSWD_SECRET_F = 'docker_registry_passwd'
_HTTP_SECRET_F = 'docker_registry_http_secret'
_PASSWD_VISIBILITY = 'channel'
_HTTP_SECRET_VISIBILITY = _PASSWD_VISIBILITY

#TODO(robnagler) how to clean registry?

def add_host(hdb, host):
    yf = db.secret_path(hdb, _PASSWD_SECRET_YAML_F, visibility=_PASSWD_VISIBILITY)
    if yf.check():
        y = pkyaml.load_file(yf)
    else:
        y = pkcollections.Dict()
    assert not host in y, \
        '{}: host already exists'
    y[host] = db.random_string()
    with open(str(yf), 'w') as f:
        yaml.dump(y, f)
    pf = db.secret_path(hdb, _PASSWD_SECRET_F, visibility=_PASSWD_VISIBILITY)
    with open(str(pf), 'a') as f:
        f.write('{}:{}\n'.format(host, bcrypt.hashpw(y[host], bcrypt.gensalt(5))))


def install_crt_and_login(compt, j2_ctx):
    update_j2_ctx(j2_ctx)
    compt.install_access(mode='700', owner=j2_ctx.docker_registry_run_u)
    compt.install_directory(_ROOT_CONFIG_JSON.dirname)
    compt.install_directory(_CERTS_D)
    d = _CERTS_D.join(j2_ctx.docker_registry_http_addr)
    compt.install_directory(d)

+++ rsconf_service_watch[$w]=docker_registry
+++ rsconf_install_file /var/lib/docker_registry/v5.bivio.biz.key
+++ local path=/var/lib/docker_registry/v5.bivio.biz.key
+++ local tmp
+++ [[ -d /var/lib/docker_registry/v5.bivio.biz.key ]]
+++ tmp=/var/lib/docker_registry/v5.bivio.biz.key-rsconf-tmp
+++ install_download /var/lib/docker_registry/v5.bivio.biz.key
/var/tmp/radia-run-19988-7514/20171115004227-rsconf.sh: line 108: /var/lib/docker_registry/v5.bivio.biz.key-rsconf-tmp: No such file or directory


    crt = component.tls_key_and_crt(j2_ctx, j2_ctx.docker_registry_host).crt
    compt.install_access(mode='400', owner=j2_ctx.docker_registry_run_u)
    compt.install_abspath(crt, d.join('ca.crt'))
    # Might be needed:
    # cp certs/domain.crt /etc/pki/ca-trust/source/anchors/myregistrydomain.com.crt
    # update-ca-trust
    yf = db.secret_path(j2_ctx, _PASSWD_SECRET_YAML_F, visibility=_PASSWD_VISIBILITY)
    y = pkyaml.load_file(yf)
    u = j2_ctx.rsconf_db_host
    p = y[u]
    j2_ctx.docker_registry_auth_b64 = base64.b64encode(u + ':' + p)
    compt.install_resource(
        'docker_registry/root_config.json',
        j2_ctx,
        _ROOT_CONFIG_JSON,
    )


def prefix_image(j2_ctx, image):
    update_j2_ctx(j2_ctx)
    if image.startswith(_DOCKER_HUB_HOST):
        return image
    return '{}/{}'.format(j2_ctx.docker_registry_http_addr, image)


def update_j2_ctx(j2_ctx):
    #TODO(robnagler) exit if already initialzed
    addr = '{}:{}'.format(j2_ctx.docker_registry_host, j2_ctx.docker_registry_port)
    j2_ctx.update(
        docker_registry_http_addr=addr,
        docker_registry_http_host='https://' + addr,
        docker_registry_run_u=j2_ctx.rsconf_db_root_u,
    )


class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        # https://docs.docker.com/registry/configuration/
        self.buildt.require_component('docker')
        run_d = systemd.docker_unit_prepare(self)
        j2_ctx = pkcollections.Dict(self.hdb)
        update_j2_ctx(j2_ctx)
        kc = self.install_tls_key_and_crt(j2_ctx.docker_registry_host, run_d)
        db_d = run_d.join(_DB_SUBDIR)
        conf_f = run_d.join('config.yml')
        j2_ctx.update(
            docker_registry_auth_htpasswd_path=run_d.join('passwd'),
            docker_registry_conf_f=conf_f,
            docker_registry_db_d=db_d,
            docker_registry_http_tls_certificate=kc.crt,
            docker_registry_http_tls_key=kc.key,
        )
        j2_ctx.docker_registry_http_secret = self.secret_path_value(
            _HTTP_SECRET_F,
            lambda x: db.random_string(x, length=64),
            visibility=_HTTP_SECRET_VISIBILITY,
        )[0]
        self.install_secret_path(
            _PASSWD_SECRET_F,
            j2_ctx.docker_registry_auth_htpasswd_path,
            gen_secret=db.random_string,
            visibility=_PASSWD_VISIBILITY,
        )
        volumes = [
            [conf_f, _GLOBAL_CONF],
        ]
        systemd.docker_unit_enable(
            self,
            # Specify pull from docker.io directly to avoid registry not yet running
            image=_DOCKER_HUB_HOST + '/library/registry:2',
            env=pkcollections.Dict(),
            cmd='',
            after=['docker.service'],
            run_u=j2_ctx.docker_registry_run_u,
        )
        self.install_access(mode='700', owner=j2_ctx.docker_registry_run_u)
        self.install_directory(db_d)
        self.install_access(mode='400', owner=j2_ctx.docker_registry_run_u)
        self.install_resource(
            'docker_registry/config.yml', j2_ctx, j2_ctx.docker_registry_conf_f)
