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

    with pkio.save_chdir(pkunit.work_dir()) as d:
        pkconfig.reset_state_for_testing(add_to_environ=PKDict(RSCONF_DB_ROOT_D='UNIT TEST'))

        from rsconf.pkcli import build
        build.default_command()
        o = pkunit.data_dir()
        for e in pkio.walk_tree(o):
            pkdlog(e)
            pkunit.file_eq(expect_path=e, actual_path=d.join(o.bestrelpath(e)))
