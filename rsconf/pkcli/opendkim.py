"""generate and list keys

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import pykern.pkio
import datetime
import re
import subprocess


def gen_key(secret_dir, domain, selector=None):
    """Generate opendkim key in db secret directory

    Args:
        secret_dir (str): directory to write to
        domain (str): domain to generate
    Returns:
        PKDict: private_f, txt_f, and selector
    """
    rv = PKDict(
        selector=selector or datetime.datetime.utcnow().strftime("%Y%m%d"),
    )
    p = pykern.pkio.mkdir_parent(pykern.pkio.py_path(secret_dir))
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
        private_f=p.join(f"{rv.selector}.private"),
        txt_f=p.join(f"{rv.selector}.txt"),
    )


def parse_txt(path):
    """Parse opendkim txt file

    Args:
        path (str): txt file
    Returns:
        PKDict: subdomain and txt
    """
    m = re.search(
        r'(\S+_domainkey).*\(\s*(".+")\s*\)',
        pykern.pkio.read_text(path),
        flags=re.DOTALL,
    )
    if not m:
        pykern.pkcli.command_error("path={} does not contain domainkey", path)
    return PKDict(
        subdomain=m.group(1),
        txt=re.sub(r"\s+", " ", m.group(2), flags=re.DOTALL),
    )
