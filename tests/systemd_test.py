"""test systemd

:copyright: Copyright (c) 2019 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_on_calendar():
    from pykern.pkcollections import PKDict
    from pykern.pkunit import pkeq, pkexcept
    from rsconf.systemd import _on_calendar
    import datetime

    jc = PKDict(
        rsconf_db=PKDict(is_almalinux9=False), systemd=PKDict(timezone="America/Denver")
    )
    d = datetime.datetime(2019, 8, 1)
    s = datetime.datetime(2019, 12, 1)
    pkeq("Sun *-*-* 6:0:0", _on_calendar("Sun 0", jc, d))
    pkeq("Sun *-*-* 7:0:0", _on_calendar("Sun 0", jc, s))
    pkeq("*-*-* 9:0:0", _on_calendar(3, jc, d))
    pkeq("*-*-* 9:0:0", _on_calendar("3", jc, d))
    pkeq("*-*-* 10:0:0", _on_calendar("3", jc, s))
    pkeq("Mon-Fri *-*-* 23:0:0", _on_calendar("Mon-Fri 17", jc, d))
    pkeq("Mon-Fri *-*-* 23:59:0", _on_calendar("Mon-Fri 17", jc, s))
    pkeq("*-*-* *:0/5:0", _on_calendar("*:0/5", jc, d))
    pkeq("*-*-* 0:0:0", _on_calendar("18", jc, d))
    pkeq("*-*-* 1:0:0", _on_calendar("18", jc, s))
    pkeq("*-*-1 12:0:0", _on_calendar("1 6", jc, d))
    pkeq("*-*-1 13:0:0", _on_calendar("1 6", jc, s))
    pkeq("*-*-* 3:30:0", _on_calendar("21:30", jc, d))
    pkeq("*-*-* 4:30:0", _on_calendar("21:30", jc, s))
    pkeq("Thu *-*-* 22:00:0", _on_calendar("Thu 16:00", jc, d))
    pkeq("Thu *-*-* 23:00:0", _on_calendar("Thu 16:00", jc, s))
    with pkexcept("midnight"):
        _on_calendar("1 18", jc, s)
    with pkexcept("midnight"):
        _on_calendar("1 18:30", jc, s)
    jc = PKDict(
        rsconf_db=PKDict(is_almalinux9=False), systemd=PKDict(timezone="America/Denver")
    )
    jc.rsconf_db.is_almalinux9 = True
    pkeq("*-*-* 3:0:0 America/Denver", _on_calendar("3", jc, d))
