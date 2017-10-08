# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from rsconf import db
from pykern import pkcollections

_DB_SUBDIR = 'db'
_TLS_BASE = 'docker_registry'
_GLOBAL_CONF = '/etc/docker/registry/config.yml'

#TODO(robnagler) how to clean registry?

def tls_crt(hdb):
    return component.tls_key_and_crt(hdb, hdb.docker_registry_host).crt


def htpasswd_auth(hdb):
    # this secret is bound to the registry for this host
    f = db.secret_base(hdb, 'docker_registery_password.yml', visibility='channel')


    import bcrypt
"2" - the first revision of BCrypt, which suffers from a minor security flaw and is generally not used anymore.
"2a" - some implementations suffered from rare security flaws, replaced by 2b.

probably needs to be "2y" - format specific to the crypt_blowfish BCrypt implementation, identical to "2b" in all but name.

"2b" - latest revision of the official BCrypt algorithm, current default.

    # output of htpassword
    # foo:$2y$05$2Z2P5HLffM./.FRB69.1CuPoiIHdv.K5/fSETVV44.81iPLVGOVp2
    # Try "2b" with docker
    # probably only need 5 turns (
    bcrypt.hashpw('foobar', bcrypt.gensalt())
    '$2b$14$5huP80t2JQr5M7.X.g0jNeOXdkqKyaNRnsgrxku7GxmQtMn0uxlsC'

    this would be a yml file that gets generated
    then the htpasswd would get generated from that in the same process
    docker_registry-v4.bivio.biz.yml
    docker_registry-v4.bivio.biz-passwd
    gen_secret=yaml file with the passwopprd

    return component.tls_key_and_crt(hdb, hdb.docker_registry_host).crt


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
        addr = '{}:{}'.format(self.hdb.docker_registry_host, self.hdb.docker_registry_port)
        j2_ctx.update(
            docker_registry_db_d=db_d,
            docker_registry_http_addr=addr
            docker_registry_http_host='https://' + addr
            docker_registry_http_tls_certificate=kc.crt,
            docker_registry_http_tls_key=kc.key,
            docker_registry_conf_f=conf_f,
        )

        docker_registry_auth_htpasswd_path,

docker run -d -p 127.0.0.1:5000:5000 --restart=always --name registry -v /reg:/var/lib/registry  -v $PWD/config/config.yml:/etc/docker/registry/config.yml registry:2

        volumes = [
            [conf_f, _GLOBAL_CONF],
        ]
        systemd.docker_unit_enable(
            self,
            # Specify pull from docker.io directly
            image='docker.io/library/registry:2',
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
