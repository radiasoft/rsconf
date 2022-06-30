# -*- coding: utf-8 -*-
"""create mariadb config

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

        self.buildt.require_component("docker")
        jc, z = self.j2_ctx_init()
        z.run_u = jc.rsconf_db.run_u
        z.run_d = systemd.docker_unit_prepare(self, jc)
        z.conf_f = z.run_d.join("my.cnf")
        z.db_d = z.run_d.join("db")
        systemd.docker_unit_enable(
            self,
            jc,
            volumes=[
                [z.conf_f, "/etc/my.cnf"],
                # hardwired in some places, not sure where, and hardwired
                # in Dockefile so just mount as an alias
                [z.db_d, "/var/lib/mysql"],
            ],
            image=docker_registry.absolute_image(self),
            # find in path (probably /usr/sbin, but might be /usr/libexec)
            cmd="mysqld",
            run_u=z.run_u,
        )
        self.install_access(mode="700", owner=z.run_u)
        self.install_directory(z.db_d)
        self.install_access(mode="400")
        self.install_resource("rs_mariadb/my.cnf", jc, z.conf_f)
        db_bkp.install_script_and_subdir(
            self,
            jc,
            run_u=z.run_u,
            run_d=z.run_d,
        )
        self.append_root_bash_with_main(jc)
        self.rsconf_service_restart()
