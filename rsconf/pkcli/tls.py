# -*- coding: utf-8 -*-
u"""SSL cert operations

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkio
import subprocess
import time


KEY_EXT = '.key'


CRT_EXT = '.crt'


def gen_self_signed_crt(basename=None, *domains):
    """Generate a self-signed certificate

    Creates the files basename.{key,crt}

    Args:
        basename (str or py.path): root of files [default: domains[0]]
        domains (tuple): list of domains

    Returns:
        dict: key, crt
    """
    first = domains[0]
    if basename is None:
        basename = first
    alt = ''
    if len(domains) > 1:
        alt = """x509_extensions = v3_req
[v3_req]
subjectAltName = {}""".format(', '.join(['DNS:' + x for x in domains[1:]]))
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
    basename = pkio.py_path(basename)
    cfg = basename + '.cfg'
    pkio.write_text(cfg, c)
    crt = basename + CRT_EXT
    key = basename + KEY_EXT
    subprocess.check_call([
        'openssl',
        'req',
        '-x509',
        '-nodes',
        '-days',
        '9999',
        '-set_serial',
        str(int(time.time())),
        '-newkey',
        'rsa:2048',
        '-sha256',
        '-keyout',
        str(key),
        '-out',
        str(crt),
        '-config',
        str(cfg),
    ])
    cfg.remove(ignore_errors=True)
    return dict(crt=crt, key=key)


def is_self_signed_crt(filename):
    """Verify if the certificate is self-signed

    Must exist or throws exception.

    Args:
        filename (str or py.path): path to crt

    Returns:
        bool: true or false
    """
    o = subprocess.output(
        ['openssl', 'verify', str(filename)],
        stderr=subprocess.STDOUT,
    )
    return 'self signed' in o


def read_crt(filename):
    """Read the certificate

    Args:
        filename (str): path to crt

    Returns:
        str: read certificate
    """
    return subprocess.check_output(
        ['openssl', 'x509', '-text', '-noout', '-in', str(filename)],
    )


def read_csr(filename):
    """Read the certificate signing request

    Args:
        filename (str): path to crt

    Returns:
        str: read certificate
    """
    return subprocess.check_output(
        ['openssl', 'req', '-text', '-noout', '-verify', '-in', str(filename)],
    )
