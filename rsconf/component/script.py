# -*- coding: utf-8 -*-
"""run arbitrary scripts with dependencies

:copyright: Copyright (c) 2023 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
import re
from pykern.pkdebug import pkdp
from rsconf import component


class T(component.T):
    def internal_build_compile(self):
        _, z = self.j2_ctx_init()
        self.buildt.require_component(@{z.get("require_components", ['base_users'])});

    def internal_build_write(self):
        self.append_root_bash(self.j2_ctx.script.bash)
