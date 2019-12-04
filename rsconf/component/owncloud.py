# -*- coding: utf-8 -*-
u"""create owncloud server config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

# Migration from 9.x to 10.x involved a few fixups, just FTR
## Output by the upgrade
#occ app:disable activity
#occ app:disable gallery
#occ app:disable files_texteditor
#occ app:disable files_pdfviewer
#occ upgrade --no-interaction
## https://github.com/owncloud/core/issues/28285
#occ migrations:execute core 20170320173955
## https://github.com/owncloud/core/issues/28510
#occ user:sync --no-interaction 'OC\User\Database'
## to files:scan, must turn off "single-user" maintenance:mode
#occ maintenance:mode --off
## https://central.owncloud.org/t/file-was-deleted-from-the-server/8002/4
#occ files:scan --no-interaction --all

class T(component.T):

    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import docker_registry
        from rsconf.component import logrotate
        from rsconf.component import nginx

        self.buildt.require_component('docker', 'nginx', 'rs_mariadb')
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
        z.conf_d = z.db_d.join('config')
        z.conf_f = z.conf_d.join('config.php')
        z.files_d = z.db_d.join('files')
        z.init_conf_f = z.run_d.join('init_config.php')
        z.log_d = z.run_d.join('log')
        z.sessions_d = z.db_d.join('sessions')
        z.log_postrotate_f = z.run_d.join('reload')
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
        for d in z.db_d, z.log_d, z.files_d, z.sessions_d, z.conf_d:
            self.install_directory(d)
        self.install_access(mode='400')
        self.install_resource('owncloud/init_config.php', j2_ctx, z.init_conf_f)
        self.install_resource('owncloud/apache.conf', j2_ctx, z.apache_conf_f)
        self.install_resource('owncloud/apache_envvars', j2_ctx, z.apache_envvars_f)
        self.install_access(mode='500')
        self.install_resource('owncloud/run.sh', j2_ctx, z.run_f)
        self.install_resource('owncloud/reload.sh', j2_ctx, z.log_postrotate_f)
        logrotate.install_conf(self, j2_ctx)
        nginx.install_vhost(
            self,
            vhost=z.domain,
            backend_host='127.0.0.1',
            backend_port=z.port,
            j2_ctx=j2_ctx,
        )
        self.append_root_bash_with_main(j2_ctx)
