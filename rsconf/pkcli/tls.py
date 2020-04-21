# -*- coding: utf-8 -*-
u"""SSL cert operations

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkcompat
from pykern import pkio
from pykern.pkdebug import pkdc, pkdp, pkdlog
import subprocess
import time
import random


_CRT = 'crt'
_CSR = 'csr'
_KEY = 'key'
CRT_EXT = '.' + _CRT
CSR_EXT = '.' + _CSR
KEY_EXT = '.' + _KEY


def gen_ca_crt(common_name, basename=None):
    """Generate a self-signed certificate authority cert and key

    Creates the files basename.{key,crt}

    Args:
        basename (str or py.path): root of files [default: domains[0]]
        domain (str): only one domain

    Returns:
        dict: key, crt
    """
    return _gen_req(_CRT, basename, (common_name,), is_ca=True)


def gen_csr_and_key(basename=None, *domains):
    """Generate a csr and key

    Creates the files basename.{csr,key}

    Args:
        basename (str or py.path): root of files [default: domains[0]]
        domains (tuple): list of domains

    Returns:
        dict: key, crt
    """
    return _gen_req(_CSR, basename, domains)


def gen_self_signed_crt(basename=None, *domains):
    """Generate a self-signed certificate

    Creates the files basename.{key,crt}

    Args:
        basename (str or py.path): root of files [default: domains[0]]
        domains (tuple): list of domains

    Returns:
        dict: key, crt
    """
    return _gen_req(_CRT, basename, domains)


def gen_signed_crt(ca_key, basename=None, *domains):
    """Generate signed cert

    Creates the files basename.{key,crt}

    Args:
        ca_key (str or py.path): root of CA key, crt is assumed to end in 'crt'
        basename (str or py.path): root of files [default: domains[0]]
        domains (tuple): list of domains

    Returns:
        dict: key, crt

    """
    ca_key = pkio.py_path(ca_key)
    res = _gen_req(_CSR, basename, domains)

    res[_CRT] = res[_KEY].new(ext=CRT_EXT)
    cfg = res[_KEY].new(ext='.cfg')
    try:
        cfg.write('[v3_req]\n{}'.format(_alt_names(domains)))
        cmd = [
            'openssl',
            'x509',
            '-req',
            '-in',
            str(res[_CSR]),
            '-CA',
            str(ca_key.new(ext=CRT_EXT)),
            '-CAkey',
            str(ca_key),
            '-extensions',
            'v3_req',
            '-extfile',
            str(cfg),
            '-out',
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
    o = _run(['openssl', 'verify', '-CAfile', str(filename), str(filename)])
    return ': ok' in o.lower()


def read_crt(filename):
    """Read the certificate

    Args:
        filename (str): path to crt

    Returns:
        str: read certificate
    """
    return _run(['openssl', 'x509', '-text', '-noout', '-in', str(filename)])


def read_csr(filename):
    """Read the certificate signing request

    Args:
        filename (str): path to crt

    Returns:
        str: read certificate
    """
    return _run(['openssl', 'req', '-text', '-noout', '-verify', '-in', str(filename)])


def _alt_names(domains):
    return 'subjectAltName = {}'.format(
        ', '.join(['DNS:' + x for x in domains]),
    )

def _gen_req(which, basename, domains, is_ca=False):
    first = domains[0]
    if not basename:
        basename = first
    basename = pkio.py_path(basename)
    if is_ca:
        # pathlen:0 means can only be used for signing certs, not for
        # signing intermediate certs.
        alt = '''x509_extensions = x509_req
[x509_req]
basicConstraints=critical,CA:true,pathlen:0'''
    else:
        # Must always provide subjectAltName except for is_ca
        # see https://github.com/urllib3/urllib3/issues/497
        # which points to RFC 2818:
        # Although the use of the Common Name is existing practice, it is deprecated and
        # Certification Authorities are encouraged to use the dNSName instead.
        alt = '{}_extensions = v3_req\n[v3_req]\n{}'.format(
            'req' if which == 'csr' else 'x509',
            _alt_names(domains),
        )
    c = '''
[req]
distinguished_name = subj
prompt = no
{}

[subj]
C = US
ST = Colorado
L = Boulder
CN = {}'''.format(alt, first)
    cfg = basename + '.cfg'
    try:
        cfg.write(c)
        key = basename + KEY_EXT
        out = basename + '.' + which
        cmd = [
            'openssl',
            'req',
            '-nodes',
            '-newkey',
            'rsa:2048',
            '-keyout',
            str(key),
            '-out',
            str(out),
            '-config',
            str(cfg),
        ]
        if which == _CRT:
            cmd += ['-x509'] + _signing_args()
        _run(cmd)
    finally:
        pkio.unchecked_remove(cfg)
    res = pkcollections.Dict(key=key)
    res[which] = out
    return res


def _run(cmd):
    try:
        pkdc('{}', ' '.join(cmd))
        return pkcompat.from_bytes(
            subprocess.check_output(cmd, stderr=subprocess.STDOUT),
        )
    except Exception as e:
        o = ''
        if hasattr(e, 'output'):
            o = pkcompat.from_bytes(e.output)
        pkdlog('command error: cmd={} error={} out={}', cmd, e, o)
        raise


def _signing_args():
    return [
        '-days',
        '9999',
        '-set_serial',
        # must be distinct number for all certificates
        # people recommend 128, but that results in an empty serial in openssl
        # so 64 bits seems enough
        str(random.SystemRandom().getrandbits(64)),
        '-sha256',
    ]
