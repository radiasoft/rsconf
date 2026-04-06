"""test named_conf

:copyright: Copyright (c) 2025 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

def test_build(monkeypatch):
    from pykern import pkconfig, pkunit, pkio
    from rsconf import named_conf

    for d in pkunit.case_dirs():
        named_conf.generate("/srv/named/db", d.join('in.py'), [], test_serial="2023111502")
