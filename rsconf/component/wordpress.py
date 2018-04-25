# -*- coding: utf-8 -*-
u"""create wordpress server config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

class T(component.T):

    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import db_bkp
        from rsconf.component import docker_registry
        from rsconf.component import logrotate
        from rsconf.component import nginx

        self.buildt.require_component('docker', 'nginx', 'mysqld', 'db_bkp')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.wordpress
        z.run_u = j2_ctx.rsconf_db.run_u
        z.run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.db_d = z.run_d.join('db')
        z.run_f = z.run_d.join('run')
        z.apache_conf_f = z.run_d.join('apache.conf')
        z.apache_envvars_f = z.run_d.join('envvars')
        # Created dynamically every run
        z.apache_run_d = '/tmp/apache2'
        z.log_d = z.run_d.join('log')
        # 127.0.0.1 assumes docker --network=host
        # If you connect to "localhost" (not 127.0.0.1) mysql fails to connect,
        # because the socket isn't there, instead of trying TCP (port supplied).
        # mysql -h localhost -P 7011 -u owncloud
        # ERROR 2002 (HY000): Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock' (2)
        z.db_ip = '127.0.0.1'
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
        for d in z.db_d, z.log_d:
            self.install_directory(d)
        self.install_access(mode='400')
        self.install_resource('owncloud/init_config.php', j2_ctx, z.init_conf_f)
        self.install_resource('owncloud/apache.conf', j2_ctx, z.apache_conf_f)
        self.install_resource('owncloud/apache_envvars', j2_ctx, z.apache_envvars_f)
        self.install_access(mode='500')
        self.install_resource('owncloud/run.sh', j2_ctx, z.run_f)
        nginx.install_vhost(
            self,
            vhost=z.domain,
            backend_host='127.0.0.1',
            backend_port=z.port,
            j2_ctx=j2_ctx,
        )
        db_bkp.install_script_and_subdir(
            self,
            j2_ctx,
            run_u=z.run_u,
            run_d=z.run_d,
        )
        #TODO(robnagler) logrotate



# https://www.digitalocean.com/community/questions/redirect-loop-with-wordpress-on-apache-with-nginx-reverse-proxy-and-https-on-ubuntu-16

# https://codex.wordpress.org/Changing_The_Site_URL
# Edit functions.php
# If you have access to the site via FTP, then this method will help you quickly get a site back up and running, if you changed those values incorrectly.
#
# 1. FTP to the site, and get a copy of the active theme's functions.php file. You're going to edit it in a simple text editor and upload it back to the site.
#
# 2. Add these two lines to the file, immediately after the initial "<?php" line.
#
# update_option( 'siteurl', 'http://example.com' );
# update_option( 'home', 'http://example.com' );
# Use your own URL instead of example.com, obviously.
#
# 3. Upload the file back to your site, in the same location. FileZilla offers a handy "edit file" function to do all of the above rapidly; if you can use that, do so.
#
# 4. Load the login or admin page a couple of times. The site should come back up.
#
#
