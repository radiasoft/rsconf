# -*- coding: utf-8 -*-
u"""SSL cert operations

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdp
from pykern import pkio
import subprocess
import time


KEY_EXT = '.key'

CRT_EXT = '.crt'

def gen_csr_and_key(basename=None, *domains):
    """Generate a csr and key

    Creates the files basename.{csr,key}

    Args:
        basename (str or py.path): root of files [default: domains[0]]
        domains (tuple): list of domains

    Returns:
        dict: key, crt
    """
    return _gen_req('csr', basename, domains)


def gen_self_signed_crt(basename=None, *domains):
    """Generate a self-signed certificate

    Creates the files basename.{key,crt}

    Args:
        basename (str or py.path): root of files [default: domains[0]]
        domains (tuple): list of domains

    Returns:
        dict: key, crt
    """
    return _gen_req(CRT_EXT[1:], basename, domains)


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
    o = subprocess.check_output(
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


def _gen_req(which, basename, domains):
    pkdp(domains)
    first = domains[0]
    if not basename:
        basename = first
    alt = ''
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
    pkio.write_text(cfg, c)
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
        out,
        '-config',
        str(cfg),
    ]
    if which == 'crt':
        cmd += [
            '-x509',
            '-days',
            '9999',
            '-set_serial',
            str(int(time.time())),
            '-sha256',
        ]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    # pkio.unchecked_remove(cfg)
    res = dict(key=key)
    res[which] = out
    return res
