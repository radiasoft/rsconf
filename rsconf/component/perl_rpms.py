"""install the perl rpms

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from rsconf import component


_COMMON_PERL_ROOTS = ("Bivio::PetShop",)
_COMMON_RPMS = ("bivio-perl", "perl-Bivio")


class T(component.T):
    def add_rpms(self, rpms=(), perl_root=None):
        """Adds `rpms` and the rpm for `perl_root` to the rpms to install

        Must be called during build_compile.

        Args:
            rpms (iterable): rpms in addition to `COMMON_RPMS` [()]
            perl_root (str): perl root of an app, e.g. Bivio::BOP [None]
        Returns:
            tuple: rpm files to watch
        """
        assert self._todo is not None, "{}: rpms already installed".format(self.name)
        r = tuple(rpms)
        if perl_root and perl_root not in _COMMON_PERL_ROOTS:
            r += ("perl-{}".format(perl_root),)
        self._todo.update(r)
        return tuple(self._rpm_file(x) for x in _COMMON_RPMS + r)

    def internal_build_compile(self):
        self.buildt.require_component("base_all")
        jc, z = self.j2_ctx_init()
        self._rpm_channel = z.setdefault("rpm_channel", jc.rsconf_db.channel)
        self._todo = set()

    def internal_build_write(self):
        self.append_root_bash("install_repo_eval biviosoftware/container-perl base")
        for r in _COMMON_RPMS + tuple(sorted(self._todo)):
            self.install_perl_rpm(self.j2_ctx, r, channel=self._rpm_channel)
        self._todo = None

    def _rpm_file(self, rpm):
        return self.rpm_file(self.j2_ctx, rpm, channel=self._rpm_channel).basename
