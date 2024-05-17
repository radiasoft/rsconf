"""test pkcli.letsencrypt

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_check_expiring():
    from pykern import pkconfig, pkjson, pkunit, pkio
    from pykern.pkdebug import pkdlog
    from pykern.pkcollections import PKDict
    from rsconf.pkcli import letsencrypt, tls

    with pkio.save_chdir(pkunit.data_dir()):
        tls._cfg.expire_days = 100
        pkunit.pkeq(("letsencrypt",), letsencrypt.check_expiring())
        tls._cfg.expire_self_signed = True
        pkunit.pkeq(("letsencrypt", "self-signed"), letsencrypt.check_expiring())
