# -*- coding: utf-8 -*-
u"""rsiviz (nginx + IndeX)

:copyright: Copyright (c) 2019 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from rsconf import systemd

class T(component.T):
    def internal_build_compile(self):
        # TODO(e-carlin): nginx
        self.buildt.require_component('docker')
        jc, z = self.j2_ctx_init()
        self.__run_d = systemd.docker_unit_prepare(self, jc)

    def internal_build_write(self):
        from rsconf.component import db_bkp
        from rsconf.component import nginx
        from rsconf.component import docker

        jc = self.j2_ctx
        z = jc[self.name]
        d = self.__run_d.join(_DB_SUBDIR)
        systemd.docker_unit_enable(
            self,
            jc,
            image=z.docker_image,
            # TODO(e-carlin): This is the default command (set by build_docker_cmd)
            # is there a way to just use it and not specify cmd?
            cmd='bash /home/vagrant/.radia-run/start',
        )
        self.install_access(mode='700', owner=jc.rsconf_db.run_u)
        self.install_directory(d)
