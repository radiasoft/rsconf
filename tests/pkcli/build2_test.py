"""test rsconf build with setup_dev

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_setup_dev():
    from pykern import pkconfig, pkdebug, pkunit

    d = pkdebug.pkdp(pkunit.empty_work_dir())
    pkconfig.reset_state_for_testing(
        {
            "RSCONF_DB_ROOT_D": str(pkdebug.pkdp(d)),
            "RSCONF_PKCLI_SETUP_DEV_UNIT_TEST": "1",
        }
    )

    from rsconf.pkcli import build

    build.default_command()
