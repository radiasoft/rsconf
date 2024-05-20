"""test pkcli opendkim

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_gen_key():
    from pykern import pkunit, pkio, pkjson
    from pykern.pkdebug import pkdlog, pkdp
    from rsconf.pkcli import opendkim

    def _named_conf():
        return pkjson.load_any(pkio.read_text(opendkim.global_path("named_conf_f")))

    # Must chdir, because db.root_d is based off pwd
    with pkunit.save_chdir_work():
        opendkim.gen_key("b.c", selector="s1")
        a = _named_conf()
        pkunit.pkeq(["b.c"], list(a.keys()))
        pkunit.pkeq(["s1._domainkey"], list(a["b.c"].keys()))
        pkunit.pkre(r'^"v=DKIM.*\w"$', a["b.c"]["s1._domainkey"])
        opendkim.gen_key("a.b.c", selector="p1")
        opendkim.gen_key("a.a.a", selector="s3")
        a = _named_conf()
        pkunit.pkeq(["a.a", "b.c"], list(a.keys()))
        pkunit.pkeq(["p1._domainkey.a", "s1._domainkey"], list(a["b.c"].keys()))
        pkunit.pkeq(["s3._domainkey.a"], list(a["a.a"].keys()))
