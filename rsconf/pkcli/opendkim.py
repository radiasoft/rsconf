"""generate and list keys

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from rsconf import db


PUBLIC_KEY_SUFFIX


def gen_key(secret_dir, domain, selector=None):
    """Generate opendkim key in db secret directory

    Args:
        secret_dir (str): directory to write to
        domain (str): domain to generate
    Returns:
        PKDict: private_key_f, public_key_f, and selector
    """
    rv = PKDict(
        selector=datetime.datetime.utcnow().strftime("%Y%m%d"),
    )
    p = pkio.mkdir_parent(pkio.py_path(secret_dir).join(domain))
    subprocess.check_call(
        (
            "opendkim-genkey",
            "-b",
            "2048",
            "-D",
            str(p),
            "-s",
            rv.selector,
            "-d",
            domain,
        ),
        stderr=subprocess.STDOUT,
        shell=False,
    )
    return rv.pkupdate(
        private_key_f=p.join(f"{rv.selector}.private"),
        public_key_f=p.join(f"{rv.selector}.txt"),
    )
