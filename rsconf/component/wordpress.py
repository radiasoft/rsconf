# -*- coding: utf-8 -*-
u"""create wordpress server config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

# TO migrate to a new site
# https://codex.wordpress.org/Changing_The_Site_URL

class T(component.T):

    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker_registry
        from rsconf.component import logrotate
        from rsconf.component import nginx

        self.buildt.require_component('docker', 'nginx', 'rs_mariadb')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.wordpress
        z.run_u = j2_ctx.rsconf_db.run_u
        z.run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.srv_d = z.run_d.join('srv')
        z.run_f = z.run_d.join('run')
        z.apache_conf_f = z.run_d.join('apache.conf')
        z.apache_envvars_f = z.run_d.join('envvars')
        # Created dynamically every run
        z.apache_run_d = '/tmp/apache2'
        z.log_d = z.run_d.join('log')
        z.ip = '127.0.0.1'
        z.setdefault('num_servers', 4)
        # 127.0.0.1 assumes docker --network=host
        # If you connect to "localhost" (not 127.0.0.1) mysql fails to connect,
        # because the socket isn't there, instead of trying TCP (port supplied).
        # mysql -h localhost -P 7011 -u owncloud
        # ERROR 2002 (HY000): Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock' (2)
        z.db_host = '{}:{}'.format(
            j2_ctx.rs_mariadb.ip,
            j2_ctx.rs_mariadb.port,
        )
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            volumes=[
                [z.apache_conf_f, '/etc/apache2/sites-enabled/000-default.conf'],
                [z.apache_envvars_f, '/etc/apache2/envvars'],
            ],
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            cmd=z.run_f,
            run_u=z.run_u,
        )
        self.install_access(mode='700', owner=z.run_u)
        for d in z.log_d, z.srv_d:
            self.install_directory(d)
        for h, v in z.vhosts.items():
            v.srv_d = z.srv_d.join(h)
            self.install_directory(v.srv_d)
        self.install_access(mode='400')
        self.install_resource('wordpress/apache_envvars', j2_ctx, z.apache_envvars_f)
        self.install_resource('wordpress/apache.conf', j2_ctx, z.apache_conf_f)
        self.install_access(mode='500')
        self.install_resource('wordpress/run.sh', j2_ctx, z.run_f)
        #TODO(robnagler) No ssl cert so have to listen manually
        nginx.update_j2_ctx_and_install_access(self, j2_ctx)
        self.install_resource(
            'wordpress/nginx.conf',
            j2_ctx,
            nginx.CONF_D.join('wordpress_common.conf'),
        )
        self.append_root_bash_with_main(j2_ctx)
        #TODO(robnagler) logrotate
