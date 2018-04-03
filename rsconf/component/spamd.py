# -*- coding: utf-8 -*-
u"""create spamassassin spamd configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio


class T(component.T):

    def internal_build(self):
        from rsconf import systemd
        from rsconf.component import network
        from rsconf.component import bop

        self.buildt.require_component('base_all')
        j2_ctx = self.hdb.j2_ctx_copy()
        network.update_j2_ctx(j2_ctx)
        bop.custom_unit_prepare(self, j2_ctx)
        systemd.custom_unit_enable(self, j2_ctx)
