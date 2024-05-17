"""test pkcli.letsencrypt

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_all():
    from pykern import pkunit, pkconfig
    from pykern.pkdebug import pkdlog, pkdp

    pkconfig.reset_state_for_testing(
        {
            "RSCONF_PKCLI_TLS_EXPIRE_SELF_SIGNED": "1",
        }
    )
    # Must chdir, because db.root_d is based off pwd
    with pkunit.save_chdir_work():
        _basic()
        _csr_and_order()
        _reorder_expiring()


def _assert_challenge(named_conf, sld, subdomain=""):
    from pykern import pkunit, pkdebug

    s = "_acme-challenge"
    if subdomain:
        s = f"{s}.{subdomain}"
    i = 0
    for k, v in named_conf[sld]:
        # May be multiple so keep checking
        if k == s:
            i += 1
            pkunit.pkre("^[\w_-]+$", v)
    if i <= 0:
        pkunit.pkfail("subdomain={} not in list={}", s, named_conf[sld])


def _assert_csr(basename):
    from pykern import pkunit
    from rsconf import db

    p = db.global_path("tls_d").join(basename)
    pkunit.pkok(p.exists(), "not existent csr={}", p)


def _basic():
    from pykern import pkunit
    from pykern.pkdebug import pkdlog, pkdp
    from rsconf import db
    from rsconf.pkcli import letsencrypt, tls

    letsencrypt.register()
    _order(["radiasoft.net"], "radiasoft.net")
    _order(["*.radiasoft.org"], "star.radiasoft.org")
    _order(
        ["first.sirepo.com", "second.sirepo.com", "third.sirepo.com"],
        "mdc.sirepo.com",
    )
    letsencrypt.gen_named_conf()
    n = _named_conf()
    _assert_challenge(n, "radiasoft.net")
    _assert_challenge(n, "radiasoft.org")
    _assert_challenge(n, "sirepo.com", "third")


def _clean():
    from rsconf.pkcli import letsencrypt

    letsencrypt.global_path("named_conf_f").remove(ignore_errors=True)
    letsencrypt.global_path("orders_d").remove(rec=True, ignore_errors=True)


def _csr_and_order():
    from pykern import pkunit
    from rsconf.pkcli import letsencrypt, tls

    _clean()
    letsencrypt.csr_and_order("*.sirepo.com")
    letsencrypt.csr_and_order(
        "one.sirepo.org",
        "two.sirepo.org",
        "three.sirepo.org",
        basename="mdc.sirepo.org",
    )
    letsencrypt.gen_named_conf()
    n = _named_conf()
    _assert_challenge(n, "sirepo.com")
    _assert_challenge(n, "sirepo.org", "two")
    _assert_csr("star.sirepo.com.csr")
    _assert_csr("mdc.sirepo.org.csr")


def _named_conf():
    from pykern import pkio, pkjson
    from rsconf.pkcli import letsencrypt

    return pkjson.load_any(pkio.read_text(letsencrypt.global_path("named_conf_f")))


def _order(domains, basename):
    from rsconf.pkcli import letsencrypt, tls
    from rsconf import db

    c = tls.gen_csr_and_key(
        *domains, basename=db.global_path("tls_d").ensure(dir=True).join(basename)
    )
    letsencrypt.order(c.csr)


def _reorder_expiring():
    from pykern import pkunit
    from rsconf import db
    from rsconf.pkcli import letsencrypt, tls

    _clean()
    p = tls._EXPIRY_DAYS
    try:
        with pkunit.pkexcept("no expiring"):
            letsencrypt.reorder_expiring()
        pkunit.pkeq(None, letsencrypt.check_expiring())
        d = db.global_path("tls_d")
        tls.gen_self_signed_crt("radiasoft.net", basename=d)
        tls._EXPIRY_DAYS = "3"
        tls.gen_self_signed_crt("sirepo.com", basename=d)
        pkunit.pkeq(("sirepo.com",), letsencrypt.check_expiring())
        r = letsencrypt.reorder_expiring()
        pkunit.pkeq(
            [letsencrypt.global_path("orders_d").join("sirepo.com.json")],
            r.orders,
        )
        pkunit.pkeq(("sirepo.com",), tuple(_named_conf().keys()))
    finally:
        tls._EXPIRY_DAYS = p
