# -*- coding: utf-8 -*-
"""manage comsol

Installing::

    groupadd -g 524 lmcomsol

    useradd -g lmcomsol -u 524 lmcomsol
    groupadd -g 525 comsol-admin
    useradd -g 525 -u 525 comsol-admin
    yum install -y webkitgtk libXtst redhat-lsb-core canberra-gtk-module gnome-classic-session gnome-terminal
    disable systemd listen on sunrpc all sockets
    comsol listens on 0.0.0.0:tcp

    On the mac, to get X11 working:
    https://github.com/ControlSystemStudio/cs-studio/issues/1828
    defaults write org.macosforge.xquartz.X11 enable_iglx -bool true

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from rsconf import component


class T(component.T):
    def internal_build(self):
        from rsconf.component import db_bkp
        from rsconf import systemd

        self.buildt.require_component("db_bkp")
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.setdefault(
            self.name,
            pkcollections.Dict(
                run_u="comsol", run_d=systemd.unit_run_d(j2_ctx, "comsol")
            ),
        )
        self.install_access(mode="700", owner=z.run_u)
        self.install_directory(z.run_d)
        db_bkp.install_script_and_subdir(
            self,
            j2_ctx,
            # db_bkp runs as root as comsol user doesn't have shell
            run_u=j2_ctx.rsconf_db.root_u,
            run_d=z.run_d,
        )
