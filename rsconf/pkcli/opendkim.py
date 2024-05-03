"""Generate opendkim key pairs and opendkim-named.json

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import datetime
import pykern.pkcli
import pykern.pkio
import pykern.pkjson
import re
import subprocess


def gen_key(key_d, named_conf_f, domain, selector=None):
    """Generate opendkim key pairs for domain in key_d

    Creates key_d/domain/selector.{txt,private}. Calls
    `gen_named_conf` when done.

    Args:
        key_d (str): directory to write to
        named_conf_f (str
        domain (str): domain to generate
        selector (str): dkim selector for key [yyyymmdd]
    Returns:
        PKDict: private_f, txt_f, and selector
    """
    k = pykern.pkio.py_path(key_d)
    subprocess.check_call(
        (
            "opendkim-genkey",
            "-b",
            "2048",
            "-D",
            str(pykern.pkio.mkdir_parent(k.join(domain))),
            "-s",
            selector or datetime.datetime.utcnow().strftime("%Y%m%d"),
            "-d",
            domain,
        ),
        stderr=subprocess.STDOUT,
        shell=False,
    )
    gen_named_conf(k, named_conf_f)


def gen_named_conf(key_d, named_conf_f):
    """Read key_d and write named_conf_f

    key_d is created by `gen_key`. named_conf_f is a list of
    domains which point to keys.

    Args:
        key_d (str): dir that contains keys
        named_conf_f (str): where to write json
    """
    pykern.pkjson.dump_pretty(_PublicKeys(key_d).as_dict(), filename=named_conf_f)


def public_key_info(path):
    """Parse DNS file (*.txt) to get key and selector


    Returns:
        PKDict: values selector and txt.
    """
    m = re.search(
        r'(\S+_domainkey).*\(\s*(".+")\s*\)',
        pykern.pkio.read_text(path),
        flags=re.DOTALL,
    )
    if not m:
        pykern.pkcli.command_error("path={} does not contain domainkey", path)
    return PKDict(
        selector=m.group(1),
        txt=re.sub(r"\s+", " ", m.group(2), flags=re.DOTALL),
    )


class _PublicKeys(PKDict):
    """All keys in secret_d organized by second level domain (sld)

    self index is sld, which contains a dict selector.subdomain
    pointing to public key txt. The dictionaries are already sorted.
    """

    def __init__(self, key_d):
        for p in pykern.pkio.walk_tree(key_d, file_re=r"\.txt$"):
            self._append(
                p.dirpath().basename,
                public_key_info(p),
            )

    def as_dict(self):
        def _content_rows(subdomains):
            return PKDict({i.subdomain: i.txt for i in subdomains})

        return PKDict({d: _content_rows(s) for d, s in self.items()})

    def _append(self, domain, key_info):
        x = domain.split(".")
        key_info.sld = ".".join(x[-2:])
        key_info.subdomain = ".".join([key_info.selector] + x[0:-2])
        self.setdefault(key_info.sld, []).append(key_info)
