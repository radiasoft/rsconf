# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import bcrypt
from rsconf import component
from rsconf import db
from pykern import pkio
from pykern import pkcollections

_DB_SUBDIR = 'db'
_TLS_BASE = 'docker_registry'
_CERTS_D = pkio.py_path('/etc/docker/certs.d')
_GLOBAL_CONF = '/etc/docker/registry/config.yml'
_ROOT_CONFIG_JSON = pkio.py_path('/root/.docker/config.json')
_DOCKER_HUB_HOST = 'docker.io'
_PASSWD_SECRET_YAML_F = 'docker_registry_passwd.yml'
_PASSWD_SECRET_F = 'docker_registry_passwd'
_PASSWD_VISIBILITY = 'channel'

#TODO(robnagler) how to clean registry?

def add_host(hdb, host)
    yf = db.secret_path(hdb, _PASSWD_SECRET_YAML_F, visibility=_PASSWD_VISIBILITY)
    if yf.check():
        y = pkyaml.load_file(yf)
    else:
        y = pkcollections.Dict()
    assert not host in y, \
        '{}: host already exists'
    y[host] = db.gen_password()
    yaml.dump(y, yf)
    pf = db.secret_path(hdb, _PASSWD_SECRET_F, visibility=_PASSWD_VISIBILITY)
    with open(str(pf), 'a') as f:
        f.write('{}:{}'.format(host, bcrypt.hashpw(p, bcrypt.gensalt(5))))


def prefix_image(hdb, image):
    if image.startswith(_DOCKER_HUB_HOST):
        return image
    return '{}/{}'.format(hdb.docker_registry_http_addr, image)


def install_crt_and_login(compt, j2_ctx):
    _common_vars(j2_ctx)
    compt.install_access(mode='700', owner=hdb.docker_registry_run_u)
    compt.install_directory(_ROOT_CONFIG_JSON.dirname)
    compt.install_directory(_CERTS_D)
    d = _CERTS_D.join(hdb.docker_registry_http_addr)
    compt.install_directory(d)
    crt = component.tls_key_and_crt(hdb, hdb.docker_registry_host).crt
    compt.install_access(mode='400', owner=hdb.docker_registry_run_u)
    compt.install_abspath(crt, d.join('ca.crt'))
    # Might be needed:
    # cp certs/domain.crt /etc/pki/ca-trust/source/anchors/myregistrydomain.com.crt
    # update-ca-trust
    yf = db.secret_path(hdb, _PASSWD_SECRET_YAML_F, visibility=_PASSWD_VISIBILITY)
    y = pkyaml.load_file(yf)
    u = compt.rsconf_db_host
    p = y[u]
    j2_ctx.docker_registry_auth_b64 = base64.b64decode(u + ':' + p)
    compt.install_resource(
        'docker_registry/root_config.json',
        j2_ctx,
        _ROOT_CONFIG_JSON,
    )
    return path


class T(component.T):

    def internal_build(self):
        # https://docs.docker.com/registry/configuration/
        self.buildt.require_component('docker')
        run_d = systemd.docker_unit_prepare(self)
        db_d = run_d.join(_DB_SUBDIR)
        tls = tls_key_and_crt(self.hdb)
        conf_f = run_d.join('config.yml')
        j2_ctx = pkcollections.Dict(self.hdb)
        run_u = self.hdb.rsconf_db_root_u
        kc = self.install_tls_key_and_crt(self.hdb.docker_registry_host, run_d)
        _common_vars(j2_ctx)
        j2_ctx.update(
            docker_registry_db_d=db_d,
            docker_registry_http_tls_certificate=kc.crt,
            docker_registry_http_tls_key=kc.key,
            docker_registry_conf_f=conf_f,
            docker_registry_auth_htpasswd_path=run_d.join('passwd')
        )

        self.install_secret_path(_PASSWD_SECRET_F, visibility='channel')


docker run -d -p 127.0.0.1:5000:5000 --restart=always --name registry -v /reg:/var/lib/registry  -v $PWD/config/config.yml:/etc/docker/registry/config.yml registry:2

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
            run_u=run_u,
        )
        self.install_access(mode='700', owner=run_u)
        self.install_directory(db_d)
        self.install_access(mode='400', owner=run_u)
        self.install_resource(
            'docker_registry/config.yml', j2_ctx, j2_ctx.docker_registry_conf_f)

# Need to add to containers/bin/build - decide if private or public
# build_docker_registry - pull has to be from the same registry
docker tag 518a41981a6a myRegistry.com/myImage
docker push myRegistry.com/myImage



        # Generate the key for the server, and install on all docker
        # servers.
openssl req \
       -newkey rsa:4096 -nodes -sha256 -keyout certs/domain.key \
         -x509 -days 365 -out certs/domain.crt
/etc/docker/certs.d/myregistrydomain.com:5000/ca.crt


        self.install_access(mode='700', owner=j2_ctx.root_u)
        self.install_directory(db_d)

$ docker run -d -p 5000:5000 --restart=always --name registry \
                -v `pwd`/config.yml:/etc/docker/registry/config.yml \
            registry:2


        self.buildt.require_component('docker')

        #TODO(robnagler) if /etc/docker changes restart daemon
        #  coordinate with main.sh which may have just started daemon
        self.append_root_bash(
           "rsconf_service_prepare '{}' '{}'".format(
                self.name,
                _DAEMON_JSON,
            ),
        )
        j2_ctx = pkcollections.Dict(self.hdb)
        j2_ctx.update(
            docker_volume_group='docker',
        )
        self.install_access(mode='700', owner=j2_ctx.root_u)
        self.install_directory('/etc/docker')
        self.install_access(mode='400', owner=j2_ctx.root_u)
        self.install_resource(
            'docker/daemon.json',
            j2_ctx,
            _DAEMON_JSON,
        )
        self.append_root_bash_with_resource(
            'docker/main.sh',
            j2_ctx,
            'docker_main',
        )
        #TODO(robnagler) add live-restore?
        # live restore: https://docs.docker.com/engine/admin/live-restore
        # "live-restore": true,
        # live-restore does interrupt network due to proxies, --net=host
n

def _common_vars(j2_ctx):
    addr = '{}:{}'.format(j2_ctx.docker_registry_host, j2_ctx.hdb.docker_registry_port)
    j2_ctx.update(
        docker_registry_http_addr=addr
        docker_registry_http_host='https://' + addr
    )
