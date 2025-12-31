"""TLS certificate operations

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern import pkcompat
from pykern import pkconfig
from pykern import pkio
from pykern import pkyaml
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdp, pkdlog, pkdformat
import cryptography.x509
import cryptography.x509.oid
import datetime
import random
import re
import subprocess
import time


_CRT = "crt"
_CSR = "csr"
_KEY = "key"
CRT_EXT = "." + _CRT
CSR_EXT = "." + _CSR
KEY_EXT = "." + _KEY
CFG_EXT = ".cfg"
_ALT_DNS_RE = re.compile(r"DNS:([^,]+)")
_EXPIRY_DAYS = "9999"


def check_expiring(authority_urn_re=None):
    """Return paths of all expiring certs in tsl directory

    Config (for testing): expire_days [14] and expire_self_signed [False].

    Args:
        authority_urn_re (re): only renew certs that match [None]
    Returns:
        tuple: names of expiring crts or None
    """
    return tuple(e.path.purebasename for e in _expiring(authority_urn_re)) or None


def db_yaml(path):
    """Generate yml from all certs in tls_d

    Args:
        path (str): where to write yml, e.g. db/tls.yml
    """

    def _map():
        return PKDict({p.purebasename: sorted(c.domains) for p, c in _read_tls_d()})

    pkyaml.dump_pretty(
        PKDict(default=PKDict(component=PKDict(tls_crt=_map()))), filename=path
    )


def download_first_crt(domain, as_dict=True):
    """Get the first certificate from domain

    Args:
        domain (str): domain to access
        as_dict (bool): output with `read_as_dict` else PEM  [True]
    Returns:
        str: first certificate in chain
    """

    def _download():
        return _run(
            [
                "openssl",
                "s_client",
                "-showcerts",
                "-servername",
                domain,
                "-connect",
                f"{domain}:443",
                "-showcerts",
            ],
            stderr=subprocess.DEVNULL,
        )

    o = _download()
    m = re.search("(-+BEGIN CERTIFICATE-+.+?-+END CERTIFICATE-+)", o, re.DOTALL)
    if not m:
        raise ValueError(pkdformat("no cert in output={}", o))
    return _crt_as_dict(pkcompat.to_bytes(m.group(1))) if as_dict else m.group(1)


def gen_ca_crt(common_name, basename=None):
    """Generate a self-signed certificate authority cert and key

    Creates the files basename.{key,crt}. If basename is a directory,
    then basename/domains[0].{key,crt}.

    Args:
        domain (str): only one domain
        basename (str or py.path): root of files [default: domains[0]]

    Returns:
        dict: key, crt
    """
    return _gen_req(_CRT, basename, (common_name,), is_ca=True)


def gen_csr(key, *domains):
    """Generate a csr from key

    Creates the csr with the same basename as key.

    Args:
        key (str): which key to use
        domains (tuple): list of domains

    Returns:
        dict: key, crt
    """
    return _gen_req(_CSR, basename=None, domains=domains, key=key)


def gen_csr_and_key(*domains, basename=None):
    """Generate a csr and key

    Creates the files basename.{key,csr}. If basename is a directory,
    then basename/domains[0].{key,csr}.

    Args:
        domains (tuple): list of domains
        basename (str or py.path): root of files [default: domains[0]]

    Returns:
        dict: key, crt
    """
    return _gen_req(_CSR, basename, domains)


def gen_csr_for_all_expiring(authority_urn_re=None):
    """Generate CSRs for all certs expiring soon

    Config (for testing): expire_days [14] and expire_self_signed [False].

    Args:
        authority_urn_re (re): only renew certs that match [None]
    Returns:
        iterable: py.paths of the csrs
    """
    return tuple(
        gen_csr(c.path.new(ext=KEY_EXT), *c.domains)
        for c in _expiring(authority_urn_re)
    )


def gen_self_signed_crt(*domains, basename=None):
    """Generate a self-signed certificate

    Creates the files basename.{key,crt}. If basename is a directory,
    then basename/domains[0].{key,crt}.

    Args:
        domains (tuple): list of domains
        basename (str or py.path): root of files [default: domains[0]]

    Returns:
        dict: key, crt
    """
    return _gen_req(_CRT, basename, domains)


def gen_signed_crt(ca_key, *domains, basename=None):
    """Generate signed cert

    Creates the files basename.{key,crt}. If basename is a directory,
    then basename/domains[0].{key,crt}.

    Args:
        ca_key (str or py.path): root of CA key, crt is assumed to end in 'crt'
        domains (tuple): list of domains
        basename (str or py.path): root of files [default: domains[0]]

    Returns:
        dict: key, crt

    """
    ca_key = pkio.py_path(ca_key)
    res = _gen_req(_CSR, basename, domains)
    res[_CRT] = res[_KEY].new(ext=CRT_EXT)
    cfg = res[_KEY].new(ext=".cfg")
    try:
        cfg.write("[v3_req]\n{}".format(_alt_names(domains)))
        cmd = [
            "openssl",
            "x509",
            "-req",
            "-in",
            str(res[_CSR]),
            "-CA",
            str(ca_key.new(ext=CRT_EXT)),
            "-CAkey",
            str(ca_key),
            "-extensions",
            "v3_req",
            "-extfile",
            str(cfg),
            "-out",
            str(res[_CRT]),
        ] + _signing_args()
        _run(cmd)
    finally:
        pkio.unchecked_remove(cfg)
    return res


def is_self_signed_crt(filename):
    """Verify if the certificate is self-signed

    Must exist or throws exception.

    Args:
        filename (str or py.path): path to crt

    Returns:
        bool: true or false
    """
    return _is_self_signed_crt(
        cryptography.x509.load_pem_x509_certificate(pkio.read_binary(filename)),
    )


def read_crt(filename):
    """Read the certificate

    Args:
        filename (str): path to crt

    Returns:
        str: read certificate
    """
    return _run(["openssl", "x509", "-text", "-noout", "-in", str(filename)])


def read_crt_as_dict(path):
    """Read the certificate for domains and expiry

    Args:
        path (str): path to crt

    Returns:
        datetime: Expiry of cert
    """

    return _crt_as_dict(pkio.read_binary(path))


def read_csr(filename):
    """Read the certificate signing request

    Args:
        filename (str): path to crt

    Returns:
        str: read certificate
    """
    return _run(["openssl", "req", "-text", "-noout", "-verify", "-in", str(filename)])


def _alt_names(domains):
    return "subjectAltName = {}".format(
        ", ".join(["DNS:" + x for x in domains]),
    )


def _crt_as_dict(value):

    def _domains(crt):
        c = crt.subject.get_attributes_for_oid(
            cryptography.x509.oid.NameOID.COMMON_NAME
        )[0].value
        yield c
        for i in crt.extensions:
            if i.oid != cryptography.x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME:
                continue
            for n in i.value:
                if isinstance(n, cryptography.x509.DNSName) and n.value != c:
                    yield n.value

    def _authority_urn(crt):
        for i in crt.extensions:
            if i.oid != cryptography.x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS:
                continue
            for x in i.value:
                if (
                    x.access_method
                    == cryptography.x509.oid.AuthorityInformationAccessOID.CA_ISSUERS
                ):
                    return x.access_location.value
        else:
            raise ValueError("No issuer AuthorityInfoAccess in crt")

    c = cryptography.x509.load_pem_x509_certificate(value)
    s = _is_self_signed_crt(c)
    return PKDict(
        authority_urn=None if s else _authority_urn(c),
        domains=tuple(_domains(c)),
        expiry=c.not_valid_after_utc.replace(tzinfo=None),
        is_self_signed=s,
    )


def _expiring(authority_urn_re):
    e = datetime.datetime.utcnow() + datetime.timedelta(days=_cfg.expire_days)
    for p, rv in _read_tls_d():
        # The logic here is complicated to allow for self-signed
        # and authority_urn_re. The former is mostly for testing,
        # but is applicable if we want to re-issue self-signed
        # certs that are expiring. Self-signed do not have an authority_urn.
        if rv.expiry <= e and (
            (
                not rv.is_self_signed
                and authority_urn_re
                and authority_urn_re.search(rv.authority_urn)
            )
            or (_cfg.expire_self_signed and rv.is_self_signed)
        ):
            yield rv.pkupdate(path=p)


def _gen_req(which, basename, domains, is_ca=False, key=None):

    def _alt():
        if is_ca:
            # pathlen:0 means can only be used for signing certs, not for
            # signing intermediate certs.
            return """x509_extensions = x509_req
[x509_req]
basicConstraints=critical,CA:true,pathlen:0
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer"""
        # Must always provide subjectAltName except for is_ca
        # see https://github.com/urllib3/urllib3/issues/497
        # which points to RFC 2818:
        # Although the use of the Common Name is existing practice, it is deprecated and
        # Certification Authorities are encouraged to use the dNSName instead.
        return (
            ("req" if which == _CSR else "x509")
            + f"_extensions = v3_req\n[v3_req]\n"
            + _alt_names(domains)
        )

    def _cfg(key_out):
        rv = key_out.key.new(ext=CFG_EXT)
        rv.write(
            f"""
[req]
distinguished_name = subj
prompt = no
{_alt()}

[subj]
C = US
ST = Colorado
L = Boulder
CN = {domains[0]}"""
        )
        return rv

    def _cmd(key_out, cfg_path):
        rv = [
            "openssl",
            "req",
            "-new",
            "-key",
            str(key_out.key),
            "-out",
            str(key_out[which]),
            "-config",
            str(cfg_path),
        ]
        if which == _CRT:
            rv += ["-x509"] + _signing_args()
        return rv

    def _gen_key():
        if key:
            return pkio.py_path(key)
        rv = _key_path()
        _run(["openssl", "genrsa", "-out", str(rv), "2048"])
        return rv

    def _key_path():
        b = domains[0]
        if basename is None:
            rv = pkio.py_path(b)
        else:
            rv = pkio.py_path(basename)
            if rv.check(dir=True):
                rv = rv.join(b)
        return rv + KEY_EXT

    rv = PKDict(key=_gen_key())
    rv[which] = rv.key.new(ext=which)
    c = None
    try:
        c = _cfg(rv)
        _run(_cmd(rv, c))
    finally:
        pkio.unchecked_remove(c)
    return rv


def _is_self_signed_crt(crt):
    return crt.issuer == crt.subject


def _read_tls_d():
    from rsconf import db

    for p in pkio.sorted_glob(db.global_path("tls_d").join("*" + CRT_EXT)):
        yield p, read_crt_as_dict(p)


def _run(cmd, stderr=subprocess.STDOUT):
    try:
        pkdc("{}", " ".join(cmd))
        return pkcompat.from_bytes(
            subprocess.check_output(cmd, stderr=stderr, stdin=subprocess.DEVNULL),
        )
    except Exception as e:
        o = ""
        if hasattr(e, "output"):
            o = pkcompat.from_bytes(e.output)
        pkdlog("command error: cmd={} error={} out={}", cmd, e, o)
        raise


def _signing_args():
    return [
        "-days",
        _EXPIRY_DAYS,
        "-set_serial",
        # must be distinct number for all certificates
        # people recommend 128, but that results in an empty serial in openssl
        # so 64 bits seems enough
        str(random.SystemRandom().getrandbits(64)),
        "-sha256",
    ]


_cfg = pkconfig.init(
    expire_days=(14, int, "gen_csr_for_all_expiring days"),
    expire_self_signed=(False, bool, "allow expiring self-signed certs"),
)
