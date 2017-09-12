# -*- coding: utf-8 -*-
u"""create systemd files

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkio
from pykern import pkcollections

_SYSTEMD_DIR = pkio.py_path('/etc/systemd/system')

def docker_unit_prepare(compt):
    """Must be first call"""
    compt.docker_unit = pkcollections.Dict(
        run_d=compt.hdb.host_run_d.join(compt.name),
        service_f=_SYSTEMD_DIR.join('{}.service'.format(compt.name)),
    )
    compt.append_root_bash(
        "rsconf_service_prepare '{}' '{}' '{}'".format(
            compt.name,
            compt.docker_unit.run_d,
            compt.docker_unit.service_f,
        ),
    )
    return compt.docker_unit.run_d


def docker_unit(compt, image, env, volumes=None, after=None):
    """Must be last call"""
    compt.docker_unit.run_d
    v = pkcollections.Dict(compt.docker_unit)
    v.run_d
    if 'TZ' not in env:
        # Tested on CentOS 7, and it does have the localtime stat problem
        # https://blog.packagecloud.io/eng/2017/02/21/set-environment-variable-save-thousands-of-system-calls/
        env['TZ'] = ':/etc/localtime'
    v.update(
        after=' '.join(after or []),
        exports='\n'.join(
            ["export '{}={}'".format(k, env[k]) for k in sorted(env.keys())],
        ),
        image=image + ':' + compt.hdb.channel,
        name=compt.name,
        run_u=compt.hdb.run_u,
    )
    v.volumes = ' '.join(
        ["-v '{}:{}'".format(x, x) for x in [v.run_d] + (volumes or [])],
    )
    scripts = ('cmd', 'env', 'remove', 'start', 'stop')
    compt.install_access(mode='700', owner=v.run_u)
    compt.install_directory(v.run_d)
    compt.install_access(mode='500')
    for s in scripts:
        v[s] = v.run_d.join(s)
        compt.install_resource('systemd/' + s, v, v[s])
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # These files should be 400, since there's no value in making them public.
    compt.install_access(mode='444', owner=compt.hdb.root_u)
    compt.install_resource(
        'systemd/service',
        v,
        compt.docker_unit.service_f,
    )
