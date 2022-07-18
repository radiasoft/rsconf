# -*- coding: utf-8 -*-
"""test systemd

:copyright: Copyright (c) 2019 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import pytest


def test_on_calendar():
    from pykern.pkunit import pkeq, pkexcept
    from rsconf.systemd import _on_calendar
    import datetime

    z = "America/Denver"
    d = datetime.datetime(2019, 8, 1)
    s = datetime.datetime(2019, 12, 1)
    pkeq("Sun *-*-* 6:0:0", _on_calendar("Sun 0", z, d))
    pkeq("Sun *-*-* 7:0:0", _on_calendar("Sun 0", z, s))
    pkeq("*-*-* 9:0:0", _on_calendar(3, z, d))
    pkeq("*-*-* 9:0:0", _on_calendar("3", z, d))
    pkeq("*-*-* 10:0:0", _on_calendar("3", z, s))
    pkeq("Mon-Fri *-*-* 23:0:0", _on_calendar("Mon-Fri 17", z, d))
    pkeq("Mon-Fri *-*-* 23:59:0", _on_calendar("Mon-Fri 17", z, s))
    pkeq("*-*-* *:0/5:0", _on_calendar("*:0/5", z, d))
    pkeq("*-*-* 0:0:0", _on_calendar("18", z, d))
    pkeq("*-*-* 1:0:0", _on_calendar("18", z, s))
    pkeq("*-*-1 12:0:0", _on_calendar("1 6", z, d))
    pkeq("*-*-1 13:0:0", _on_calendar("1 6", z, s))
    pkeq("*-*-* 3:30:0", _on_calendar("21:30", z, d))
    pkeq("*-*-* 4:30:0", _on_calendar("21:30", z, s))
    pkeq("Thu *-*-* 22:00:0", _on_calendar("Thu 16:00", z, d))
    pkeq("Thu *-*-* 23:00:0", _on_calendar("Thu 16:00", z, s))
    with pkexcept("midnight"):
        _on_calendar("1 18", z, s)
    with pkexcept("midnight"):
        _on_calendar("1 18:30", z, s)
