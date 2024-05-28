"""test pkcli tls

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_read_crt_as_dict():
    from pykern import pkunit
    from pykern.pkdebug import pkdlog, pkdp
    from rsconf.pkcli import tls
    import datetime

    f = pkunit.data_dir().join("radiasoft.net.crt")
    pkunit.pkok(not tls.is_self_signed_crt(f), "crt={} is self-signed", f)
    a = tls.read_crt_as_dict(f)
    pkunit.pkeq(
        datetime.datetime(2024, 12, 4, 23, 59, 59),
        a.expiry,
    )


def test_self_signed_and_expiry():
    from pykern import pkunit, pkio
    from pykern.pkdebug import pkdlog, pkdp
    from rsconf.pkcli import tls
    import datetime

    with pkunit.save_chdir_work():
        domains = ("c.c", "b.b", "a.a")
        c = tls.gen_self_signed_crt(*domains)
        pkunit.pkok(
            tls.is_self_signed_crt(c.crt),
            "crt={} is not self-signed",
            c.crt,
        )
        pkunit.pkeq("c.c.crt", c.crt.basename)
        a = tls.read_crt_as_dict(c.crt)
        e = datetime.datetime.utcnow() + datetime.timedelta(
            days=int(tls._EXPIRY_DAYS) - 1
        )
        pkunit.pkok(e < a.expiry, "expect={} >= actual={}", e, a.expiry)
        pkunit.pkeq(domains, a.domains)


def test_db_yaml():
    from pykern import pkunit, pkio, pkyaml
    from pykern.pkdebug import pkdlog, pkdp
    from rsconf.pkcli import tls

    with pkunit.save_chdir_work():
        with pkio.save_chdir("db/secret/tls", mkdir=True):
            tls.gen_self_signed_crt("c.c", "b.b", "a.a")
            tls.gen_self_signed_crt("d.d")
        tls.db_yaml("out.yml")
        pkunit.file_eq("out.yml")
