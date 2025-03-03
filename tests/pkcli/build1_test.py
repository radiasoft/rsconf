"""test rsconf build

:copyright: Copyright (c) 2021 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_build(monkeypatch):
    import socket

    original_gethostbyname = socket.gethostbyname

    def _gethostbyname(host):
        if host == "user-1.radia.run":
            # Must be valid ip
            return "10.10.10.99"
        return original_gethostbyname(host)

    monkeypatch.setattr(socket, "gethostbyname", _gethostbyname)

    from pykern import pkconfig, pkunit, pkio
    from pykern.pkdebug import pkdlog
    from pykern.pkcollections import PKDict
    from rsconf.pkcli import build

    try:
        for d in pkunit.case_dirs():
            pkio.mkdir_parent(d.join("srv"))
            build.default_command()
    except Exception:
        pkdlog(
            """**RSCONF DEVELOPERS**
If you get an error caused by the hash in a component.sh file,
update the component.sh file to see what changed in the file to be downloaded."""
        )
        raise
