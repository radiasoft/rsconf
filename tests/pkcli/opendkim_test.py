"""test pkcli opendkim

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_gen_key():
    from pykern import pkunit, pkio, pkjson
    from pykern.pkdebug import pkdlog, pkdp
    from rsconf.pkcli import opendkim

    d = pkunit.empty_work_dir()
    n = d.join("opendkim-named.json")
    k = d.join("keys")
    opendkim.gen_key(k, n, "b.c", selector="s1")
    a = pkjson.load_any(pkio.read_text(n))
    pkunit.pkeq(["b.c"], list(a.keys()))
    pkunit.pkeq(["s1._domainkey"], list(a["b.c"].keys()))
    pkunit.pkre(r'^"v=DKIM.*\w"$', a["b.c"]["s1._domainkey"])
    opendkim.gen_key(k, n, "a.b.c", selector="p1")
    opendkim.gen_key(k, n, "a.a.a", selector="s3")
    a = pkjson.load_any(pkio.read_text(n))
    pkunit.pkeq(["a.a", "b.c"], list(a.keys()))
    pkunit.pkeq(["p1._domainkey.a", "s1._domainkey"], list(a["b.c"].keys()))
    pkunit.pkeq(["s3._domainkey.a"], list(a["a.a"].keys()))
