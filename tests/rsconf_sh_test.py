"""test rsconf.sh

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_yum_install():
    import rsconf
    import subprocess
    from pykern import pkresource, pkunit

    with pkunit.save_chdir_work():
        pkunit.file_eq(
            "yum_install.out",
            actual=subprocess.check_output(
                [
                    "bash",
                    str(pkunit.data_dir().join("driver.sh")),
                    pkresource.filename("rsconf/rsconf.sh", rsconf),
                ],
                stderr=subprocess.STDOUT,
            ).decode(),
        )
