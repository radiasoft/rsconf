# -*- coding: utf-8 -*-
u"""?

:copyright: Copyright (c) 2018 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component

class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        self.buildt.require_component('base_os')
        self.buildt.require_component('network')
        self.buildt.require_component('base_users')
        self.buildt.require_component('logrotate')
        self.append_root_bash(': nothing to do')
