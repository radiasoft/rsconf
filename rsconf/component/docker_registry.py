# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

_DB_SUBDIR = 'db'
_TLS_BASE = 'docker_registry'
_GLOBAL_CONF = '/etc/docker/registry/config.yml'

#TODO(robnagler) how to clean registry?

def tls_crt(hdb):
    return component.tls_key_and_crt(hdb, hdb.docker_registry_host).crt

def htpasswd_auth(hdb):
    # this secret is bound to the registry for this host
    this would be a yml file that gets generated
    then the htpasswd would get generated from that in the same process
    docker_registry-v4.bivio.biz.yml
    docker_registry-v4.bivio.biz-passwd
    gen_secret=yaml file with the password
    return component.tls_key_and_crt(hdb, hdb.docker_registry_host).crt


class T(component.T):

    def internal_build(self):
        self.buildt.require_component('docker')

        run_d = systemd.docker_unit_prepare(self)
        db_d = run_d.join(_DB_SUBDIR)
        tls = tls_key_and_crt(self.hdb)
        conf_f = run_d.join('config.yml')

        j2_ctx = pkcollections.Dict(self.hdb)
        run_u = self.hdb.rsconf_db_root_u
        self.install_access(mode='400', owner=run_u)
        self.install_resource('docker_registry/config.yml', j2_ctx, conf_f)
        kc = self.install_tls_key_and_crt(self.hdb.docker_registry_host, run_d)
        j2_ctx.update(
            docker_registry_http_tls_certificate=kc.crt,
            docker_registry_http_tls_key=kc.key,
        )
        volumes = [
            [conf_f, _GLOBAL_CONF],
        ]

        docker_registry_db_d
        # https://docs.docker.com/registry/configuration/

# Need to add to containers/bin/build - decide if private or public
# build_docker_registry - pull has to be from the same registry
docker tag 518a41981a6a myRegistry.com/myImage
docker push myRegistry.com/myImage

        docker_registry_auth_htpasswd_path
        docker_registry_http_addr v5.bivio.biz:{port}
        docker_registry_http_host https://v5.bivio.biz:{port}
        docker_registry_http_secret
        docker_registry_http_tls_key - generate for dev
        docker_registry_http_tls_certificate



        # Generate the key for the server, and install on all docker
        # servers.
openssl req \
       -newkey rsa:4096 -nodes -sha256 -keyout certs/domain.key \
         -x509 -days 365 -out certs/domain.crt
/etc/docker/certs.d/myregistrydomain.com:5000/ca.crt


        self.install_access(mode='700', owner=j2_ctx.root_u)
        self.install_directory(db_d)

docker run -d -p 127.0.0.1:5000:5000 --restart=always --name registry -v /reg:/var/lib/registry  -v $PWD/config/config.yml:/etc/docker/registry/config.yml registry:2

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
