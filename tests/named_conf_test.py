"""test named_conf

:copyright: Copyright (c) 2025 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_build():
    from pykern import pkunit, pkio
    from rsconf import named_conf
    import shutil, subprocess

    for d in pkunit.case_dirs():
        named_conf.generate(
            str(d),
            d.join("in.py"),
            pkio.sorted_glob("*.json"),
            test_serial="2023111502",
        )
        if x := shutil.which("named-checkconf"):
            subprocess.check_call([x, "-z", "named.conf"])
        f = d.join("named.conf")
        pkio.write_text(f, pkio.read_text(f).replace(str(d), "/srv/named/db"))
