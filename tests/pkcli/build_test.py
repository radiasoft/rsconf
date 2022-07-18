# -*- coding: utf-8 -*-
"""test rsconf build

:copyright: Copyright (c) 2021 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
import pytest


def test_build():
    from pykern import pkconfig, pkunit, pkio
    from pykern.pkdebug import pkdlog
    from pykern.pkcollections import PKDict
    from rsconf.pkcli import build
    from rsconf import db

    pkdlog("""
If you get an error caused by the hash in a component.sh file,
update the component.sh file to see what changed in the file to be downloaded.
    """)
    for d in pkunit.case_dirs():
        db.cfg.fconf = "fconf" in d.basename
        pkio.mkdir_parent(d.join("srv"))
        build.default_command()
