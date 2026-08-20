"""install the perl rpms shared by all bop components

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from rsconf import component


class T(component.T):
    def internal_build_compile(self):
        from rsconf.component import bop

        self.buildt.require_component("base_all")
        bop.install_common_perl_rpms(self, self.hdb.j2_ctx_copy())
