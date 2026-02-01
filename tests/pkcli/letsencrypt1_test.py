"""test pkcli.letsencrypt

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

_MOCK_PEM = "simple PEM sentinel; can be anything"


def setup_module():
    from acme import client, errors
    from pykern import pkconfig, pkunit
    from pykern.pkcollections import PKDict

    f = getattr(client.ClientV2, "poll_and_finalize")

    def _mock(*args, **kwargs):
        # Sanity check that it doesn't work
        with pkunit.pkexcept(errors.ValidationError):
            f(*args, **kwargs)
        # Return what letsencrypt needs
        return PKDict(fullchain_pem=_MOCK_PEM)

    setattr(client.ClientV2, "poll_and_finalize", _mock)
    pkconfig.reset_state_for_testing(
        {
            "RSCONF_PKCLI_TLS_EXPIRE_SELF_SIGNED": "1",
        }
    )


def test_all():
    from pykern import pkunit
    from pykern.pkdebug import pkdlog, pkdp

    # Must chdir, because db.root_d is based off pwd
    with pkunit.save_chdir_work():
        _basic()
        _new_orders_and_reordering()


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
            pkunit.pkre(r"^[\w_-]+$", v)
    if i <= 0:
        pkunit.pkfail("subdomain={} not in list={}", s, named_conf[sld])


def _assert_path(basename_or_path, expect=True):
    from pykern import pkunit
    from rsconf import db

    p = (
        basename_or_path
        if hasattr(basename_or_path, "exists")
        else _tls_path(basename_or_path)
    )
    pkunit.pkeq(
        expect,
        p.exists(),
        "{} path={}",
        "missing" if expect else "not removed",
        p,
    )


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
    letsencrypt.finalize_orders()
    _assert_path("radiasoft.net.crt")
    _assert_path("star.radiasoft.org.crt")
    _assert_path("mdc.sirepo.com.crt")
    _assert_path("radiasoft.net.csr", expect=False)
    _assert_path("star.radiasoft.org.csr", expect=False)
    _assert_path("mdc.sirepo.com.csr", expect=False)
    _assert_path(letsencrypt.global_path("named_conf_f"), expect=False)


def _new_orders_and_reordering():
    from pykern import pkio, pkunit
    from rsconf import db
    from rsconf.pkcli import letsencrypt, tls

    def _change_authority():
        d = db.global_path("tls_d")
        tls.gen_self_signed_crt(
            "one.radiasoft.org", "two.radiasoft.org", basename=d.join("mdc1")
        )
        letsencrypt.order_with_crt("mdc1")
        letsencrypt.order_with_key(
            "radiasoft.net",
            "1.radiasoft.net",
            "2.radiasoft.net",
        )
        letsencrypt.gen_named_conf()
        _assert_challenge(_named_conf(), "radiasoft.org", "two")
        _assert_challenge(_named_conf(), "radiasoft.net", "2")

    def _clean(everything=False):
        pkio.unchecked_remove(letsencrypt.global_path("named_conf_f"))
        pkio.unchecked_remove(letsencrypt.global_path("orders_d"))
        if everything:
            pkio.unchecked_remove(db.global_path("tls_d"))

    def _order_with_new_csr_and_key():
        letsencrypt.order_with_new_csr_and_key("*.sirepo.com")
        letsencrypt.order_with_new_csr_and_key(
            "one.sirepo.org",
            "two.sirepo.org",
            "three.sirepo.org",
            basename="mdc.sirepo.org",
        )
        letsencrypt.gen_named_conf()
        n = _named_conf()
        _assert_challenge(n, "sirepo.com")
        _assert_challenge(n, "sirepo.org", "two")
        _assert_path("star.sirepo.com.csr")
        _assert_path("mdc.sirepo.org.csr")

    def _reorder_expiring():
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

    _clean(everything=True)
    _order_with_new_csr_and_key()
    _clean()
    _reorder_expiring()
    _clean()
    _change_authority()


def _named_conf():
    from pykern import pkio, pkjson
    from rsconf.pkcli import letsencrypt

    return pkjson.load_any(pkio.read_text(letsencrypt.global_path("named_conf_f")))


def _order(domains, basename):
    from rsconf.pkcli import letsencrypt, tls

    c = tls.gen_csr_and_key(*domains, basename=_tls_path(basename))
    letsencrypt.order(c.csr)


def _tls_path(basename):
    from rsconf import db

    return db.global_path("tls_d").ensure(dir=True).join(basename)
