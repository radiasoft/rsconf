# -*- coding: utf-8 -*-
u"""create owncloud server config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

class T(component.T):

    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import nginx
        from rsconf.component import docker_registry

        self.buildt.require_component('docker', 'nginx')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.owncloud
        z.run_u = j2_ctx.rsconf_db.run_u
        z.run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.db_d = z.run_d.join('db')
        z.run_f = z.run_d.join('run')
        z.apache_conf_f = z.run_d.join('apache.conf')
        z.apache_envvars_f = z.run_d.join('envvars')
        # Created dynamically every run
        z.apache_run_d = '/tmp/apache2'
        z.apps_d = z.db_d.join('apps')
        z.conf_d = z.db_d.join('config')
        z.conf_f = z.conf_d.join('config.php')
        z.files_d = z.db_d.join('files')
        z.init_conf_f = z.run_d.join('init_config.php')
        z.log_d = z.run_d.join('log')
        z.sessions_d = z.db_d.join('sessions')
        # assumes docker --network=host
        z.db_host = 'localhost:{}'.format(j2_ctx.owncloud_mariadb.port)
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            volumes=[
                # /mnt/data/sessions is hardwired in
                # /etc/php/7.0/mods-available/owncloud.ini. We could overrided
                # but this is just as easy, and likely to make other things work
                # that are hardwired.
                [z.db_d, '/mnt/data'],
                [z.conf_d, '/var/www/owncloud/config'],
                [z.apache_conf_f, '/etc/apache2/sites-enabled/000-default.conf'],
                [z.apache_envvars_f, '/etc/apache2/envvars'],
            ],
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            cmd=z.run_f,
            run_u=z.run_u,
        )
        self.install_access(mode='700', owner=z.run_u)
        for d in z.db_d, z.log_d, z.apps_d, z.files_d, z.sessions_d, z.conf_d:
            self.install_directory(d)
        self.install_access(mode='400')
        self.install_resource('owncloud/init_config.php', j2_ctx, z.init_conf_f)
        self.install_resource('owncloud/apache.conf', j2_ctx, z.apache_conf_f)
        self.install_resource('owncloud/apache_envvars', j2_ctx, z.apache_envvars_f)
        self.install_access(mode='500')
        self.install_resource('owncloud/run.sh', j2_ctx, z.run_f)
        #TODO(robnagler) logrotate
        nginx.install_vhost(
            self,
            vhost=z.domain,
            backend_host='localhost',
            backend_port=z.port,
            j2_ctx=j2_ctx,
        )
