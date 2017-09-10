# -*- coding: utf-8 -*-
u"""create systemd files

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkio
from pykern import pkcollections

SYSTEMD_DIR = pkio.py_path('/etc/systemd/system')


def docker_unit_prepare(compt):
    """Must be first call"""
    compt.append_root_bash("rsconf_prepare_service '{}'".format(compt.name))
    compt.docker_unit_run_d = compt.hdb.host_run_d.join(compt.name)
    return compt.docker_unit_run_d


def docker_unit(compt, image, env, volumes=None, after=None):
    """Must be last call"""

    v = pkcollections.Dict(
        name=compt.name,
        run_u=compt.hdb.run_u,
        # Asserts that docker_unit_prepare was called
        run_d=compt.docker_unit_run_d,
    )
    v.exports = '\n'.join(
        ["export '{}={}'".format(k, env[k]) for k in sorted(env.keys())],
    )
    v.volumes = ' '.join(["-v '{}:{}'".format(x, x) for x in [v.run_d] + (volumes or [])])
    v.image = image + ':' + compt.hdb.channel
    v.after = ' '.join(after or [])
    compt.install_access(mode=700, owner=v.run_u)
    compt.install_dir(v.run_d)
    compt.install_access(mode=500)
    scripts = ('cmd', 'env', 'remove', 'start', 'stop')
    for s in scripts:
        v[s] = run_d.join(s)
        compt.install_resource('docker_unit/' + s, v, value[s])
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # I would want these files to be 400, since there's no value in making them
    # public. The machines are inaccessiable to anybody who doesn't have root access.
    compt.install_access(mode=444, owner=v.root_u)
    compt.install_resource(
        'docker_unit/service',
        values=values,
        SYSTEMD_DIR.join('{}.service'.format(compt.name))
    )
    compt.append_root_bash("rsconf_commit_service '{}'".format(compt.name))
