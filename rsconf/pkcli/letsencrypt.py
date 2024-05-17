"""Implement letsencrypt protocol in three steps

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import acme.messages
import pykern.pkcli
import pykern.pkconfig
import pykern.pkio
import pykern.pkjson
import re
import rsconf.db
import rsconf.pkcli.tls

_AUTHORITY_URN_RE = re.compile(r"lencr\.org")


def check_expiring():
    """Check for expiring letsencrypt certs

    Returns:
        tuple: names of expiring certs
    """
    return rsconf.pkcli.tls.check_expiring(authority_urn_re=_AUTHORITY_URN_RE)


def csr_and_order(*domains, basename=None):
    """Generates csr and key for domains and creates order

    Wildcard certs must be a single domain. The cert will include the
    higher level domain, e.g. ``*.example.com`` will have
    ``example.com`` added to the CSR. The cert will be named
    ``star.<domain>``, e.g. ``star.example.com``.

    If there are multiple domains (except for wildcard case),
    `basename` must be provided.

    Otherwise, the basename is the single domain case, the csr
    basename is the domain.

    Args:
        domains (tuple): list of domains for cert
        basename (str): for file name for multidomain certs only [None]
    Returns:
        py.path: order created

    """

    if len(domains) > 1:
        if not basename:
            pykern.pkcli.command_error(
                "multi-domain cert requires basename; domains={}", domains
            )
        b = basename
    elif domains[0].startswith("*"):
        f = domains[0][2:]
        domains = (domains[0], f)
        b = "star." + f
    else:
        b = domains[0]
    c = rsconf.pkcli.tls.gen_csr_and_key(
        *domains, basename=rsconf.db.global_path("tls_d").ensure(dir=True).join(b)
    )
    return order(c.csr)


def finalize_orders():
    """Answers all challenges and saved certs

    Removes orders as they are answered. Removes named_conf_f once all
    certs are written.
    """

    def _remove_csr_and_return_crt(order):
        rv = (
            rsconf.db.global_path("tls_d")
            .join(order.path.basename)
            .new(ext=rsconf.pkcli.tls.CRT_EXT)
        )
        pykern.pkio.unchecked_remove(rv.new(ext=rsconf.pkcli.tls.CSR_EXT))
        return rv

    c = _client()
    rv = []
    for o in _iter_orders():
        for g in _iter_challenges(o):
            c.answer_challenge(g.resource, g.resource.response(c.net.key))
        p = _remove_csr_and_return_crt(o)
        pykern.pkio.write_text(
            p,
            c.poll_and_finalize(o.resource).fullchain_pem,
        )
        pykern.pkio.unchecked_remove(o.path)
        rv.append(p)
    pykern.pkio.unchecked_remove(global_path("named_conf_f"))
    return rv


def gen_named_conf():
    """Generate the letsencrypt-named.conf from existing orders

    Asserts that the file does not exist already.

    Returns:
        py.path: file that was generated
    """
    rv = _assert_named_conf_not_exists()
    pykern.pkjson.dump_pretty(_Orders().as_dict, filename=rv)
    return rv


def global_path(name):
    """Return path for name

    Args:
        name (str): "account_f", "account_key_f", and "orders_d"
    Returns:
        py.path: corresponding to name
    """

    def _dir(name, sub_dir=None):
        rv = rsconf.db.global_path(name)
        if sub_dir:
            rv = rv.join(sub_dir)
        return rv.ensure(dir=True)

    if name == "named_conf_f":
        # POSIT: Bivio::Util::NamedConf looks for ``*-named.json``
        return _dir("etc_d").join("letsencrypt-named.json")
    if name == "orders_d":
        return _dir("tmp_d", "letsencrypt")
    d = _dir("secret_d", "letsencrypt")
    if name == "account_f":
        return d.join("account.json")
    if name == "account_key_f":
        return d.join("account.pem")
    raise AssertionError(f"invalid name={name}")


def order(csr_path):
    """Generate a single order for `csr_path`

    Args:
        csr_path (str): which CSR
    Returns:
        py.path: file that contains serialized order
    """
    p = pykern.pkio.py_path(csr_path)
    rv = global_path("orders_d").join(p.basename).new(ext="json")
    if rv.exists():
        pykern.pkcli.command_error(
            "existing order={}; orders may need to be purged", rv
        )
    o = _client().new_order(p.read_binary())
    pykern.pkio.write_text(rv, o.json_dumps_pretty())
    return rv


def register():
    """Register a new account

    Asserts that an account.json doesn't already exist.

    Returns:
        str: account uri for letsenrypt
    """
    f = global_path("account_f")
    if f.exists():
        pykern.pkcli.command_error(
            "already registered; to re-register remove path={}", f
        )
    r = _client(is_register=True).new_account(
        acme.messages.NewRegistration.from_data(
            terms_of_service_agreed=True,
        ),
    )
    pykern.pkio.write_text(f, r.json_dumps_pretty())
    return r.uri


def reorder_expiring():
    """Place orders for expiring certs

    Only matches letsenrypt certs.

    Raises:
        CommandError: when there are no expiring certs
    Returns:
        PKDict: list of order paths and named_conf path.
    """
    _assert_named_conf_not_exists()
    rv = PKDict(
        orders=[
            order(c.csr)
            for c in rsconf.pkcli.tls.gen_csr_for_all_expiring(
                authority_urn_re=_AUTHORITY_URN_RE
            )
        ]
    )
    if not rv.orders:
        pykern.pkcli.command_error("No expiring certs")
    rv.named_conf = gen_named_conf()
    return rv


class _Orders:
    """Create a dictionary of all existing orders"""

    def __init__(self):
        self.as_dict = PKDict()
        self._key = _client().net.key
        for o in _iter_orders():
            for c in _iter_challenges(o):
                self._challenge(o, c)

    def _challenge(self, order, challenge):
        def _add(sld, subdomain):
            self.as_dict.setdefault(sld, []).append(
                (subdomain, challenge.resource.validation(self._key))
            )

        n = ["_acme-challenge"] + challenge.domain.split(".")
        _add(".".join(n[-2:]), ".".join(n[0:-2]))


def _assert_named_conf_not_exists():
    f = global_path("named_conf_f")
    if f.exists():
        pykern.pkcli.command_error(
            "existing named_conf={}; please remove and check orders={}",
            f,
            global_path("orders_d"),
        )
    return f


def _client(is_register=False):
    from acme import client
    import josepy

    def _account_key():
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat import backends

        k = global_path("account_key_f")
        if k.exists():
            return serialization.load_pem_private_key(
                k.read_binary(),
                password=None,
            )
        rv = rsa.generate_private_key(
            backend=backends.default_backend(),
            key_size=2048,
            public_exponent=65537,
        )
        k.write_binary(
            rv.private_bytes(
                encoding=serialization.Encoding.PEM,
                encryption_algorithm=serialization.NoEncryption(),
                format=serialization.PrivateFormat.PKCS8,
            ),
        )
        return rv

    def _directory_uri():
        return (
            "https://acme-v02.api.letsencrypt.org/directory"
            if pykern.pkconfig.channel_in("prod")
            else "https://acme-staging-v02.api.letsencrypt.org/directory"
        )

    k = PKDict()
    if not is_register:
        k.account = acme.messages.RegistrationResource().json_loads(
            global_path("account_f").read_binary()
        )
    n = client.ClientNetwork(
        key=josepy.JWKRSA(key=_account_key()),
        user_agent="git.radiasoft.org/rsconf",
        **k,
    )
    return client.ClientV2(
        directory=client.ClientV2.get_directory(_directory_uri(), n),
        net=n,
    )


def _iter_challenges(order):
    def _find_dns(authorization):
        d = authorization.body.identifier.value
        for c in authorization.body.challenges:
            if isinstance(c.chall, acme.challenges.DNS01):
                return PKDict(resource=c, domain=d)
        else:
            raise ValueError(f"no dns challenges for domain={d}")

    for a in order.resource.authorizations:
        yield _find_dns(a)


def _iter_orders():
    def _order(order_f):
        return PKDict(
            path=order_f,
            resource=acme.messages.OrderResource.json_loads(order_f.read_binary()),
        )

    for f in pykern.pkio.sorted_glob(global_path("orders_d").join("*").new(ext="json")):
        yield _order(f)
