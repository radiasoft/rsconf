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
import rsconf.db
import re
import subprocess


def gen_key(domain, selector=None):
    """Generate opendkim key pairs for domain in key_d

    Creates key_d/domain/selector.{txt,private}. Calls
    `gen_named_conf` when done.

    Args:
        domain (str): domain to generate
        selector (str): dkim selector for key [yyyymmdd]
    Returns:
        PKDict: private_f, txt_f, and selector
    """
    subprocess.check_call(
        (
            "opendkim-genkey",
            "-b",
            "2048",
            "-D",
            str(pykern.pkio.mkdir_parent(global_path("key_d").join(domain))),
            "-s",
            selector or datetime.datetime.utcnow().strftime("%Y%m%d"),
            "-d",
            domain,
        ),
        stderr=subprocess.STDOUT,
        shell=False,
    )
    gen_named_conf()


def gen_named_conf():
    """Read key_d and write `NAMED_CONF_F`

    key_d is created by `gen_key`. `NAMED_CONF_F` is a list of
    domains which point to keys.
    """
    pykern.pkjson.dump_pretty(
        _PublicKeys(global_path("key_d")).as_dict(),
        filename=global_path("named_conf_f"),
    )


def global_path(name):
    """Return path for name

    Args:
        name (str): "named_conf_f" or "key_d"
    Returns:
        py.path: corresponding to name
    """
    if name == "key_d":
        return rsconf.db.global_path("secret_d").join("opendkim").ensure(dir=True)
    elif name == "named_conf_f":
        # POSIT: Bivio::Util::NamedConf looks for ``*-named.json``
        return (
            rsconf.db.global_path("etc_d").ensure(dir=True).join("opendkim-named.json")
        )
    else:
        raise AssertionError(f"invalid name={name}")


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
    """All keys in `key_d` organized by second level domain (sld)

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
