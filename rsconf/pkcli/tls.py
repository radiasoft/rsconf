# -*- coding: utf-8 -*-
u"""SSL cert operations

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkio
from pykern.pkdebug import pkdc, pkdp, pkdlog
import subprocess
import time


_CRT = 'crt'
_CSR = 'csr'
_KEY = 'key'
CRT_EXT = '.' + _CRT
CSR_EXT = '.' + _CSR
KEY_EXT = '.' + _KEY


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
        '-out',
        str(res[_CRT]),
    ] + _signing_args()
    _run(cmd)
    return res


def is_self_signed_crt(filename):
    """Verify if the certificate is self-signed

    Must exist or throws exception.

    Args:
        filename (str or py.path): path to crt

    Returns:
        bool: true or false
    """
    # error 18 at 0 depth lookup:self signed certificate
    # Root certs are self-signed
    o = _run(['openssl', 'verify', str(filename)])
    return 'self signed' in o


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


def _gen_req(which, basename, domains):
    first = domains[0]
    if not basename:
        basename = first
    alt = ''
    basename = pkio.py_path(basename)
    if len(domains) > 1:
        alt = """{}_extensions = v3_req
[v3_req]
subjectAltName = {}""".format(
    'req' if which == 'csr' else 'x509',
    ', '.join(['DNS:' + x for x in domains[1:]]))
    c = """
[req]
distinguished_name = subj
prompt = no
{}

[subj]
C = US
ST = Colorado
L = Boulder
CN = {}""".format(alt, first)
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
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except Exception as e:
        o = ''
        if hasattr(e, 'output'):
            o = e.output
        pkdlog('command error: cmd={} error={} out={}', cmd, e, o)
        raise


def _signing_args():
    return [
        '-days',
        '9999',
        '-set_serial',
        str(int(time.time())),
        '-sha256',
    ]
