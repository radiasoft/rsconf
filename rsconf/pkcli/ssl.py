# -*- coding: utf-8 -*-
u"""SSL cert operations

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function


def read_crt(filename):
    """Read the certificate

    Args:
        filename (str): path to crt

    Returns:
        str: read certificate
    """
    import subprocess

    return subprocess.check_output(['openssl', 'x509', '-text', '-noout', '-in', filename])


def read_csr(filename):
    """Read the certificate signing request

    Args:
        filename (str): path to crt

    Returns:
        str: read certificate
    """
    import subprocess

    return subprocess.check_output(['openssl', 'req', '-text', '-noout', '-verify', '-in', filename])


def create_crt(basename=None, *domains):
    """Generate a self-signed certificate

    Creates the files domain.{csr,key,crt}

    Args:
        basename (str): to be used to generate file names
        domains (tuple): list of domains
    """
    from pykern import pkio
    import subprocess
    import time

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
    cfg = basename + '.cfg'
    pkio.write_text(cfg, c)
    crt = basename + '.crt'
    key = basename + '.key'
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
        key,
        '-out',
        crt,
        '-config',
        cfg,
    ])
    return dict(cfg=cfg, crt=crt, key=key)
