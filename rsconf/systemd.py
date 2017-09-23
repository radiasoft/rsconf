# -*- coding: utf-8 -*-
u"""create systemd files

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkio
from pykern import pkcollections


_SYSTEMD_DIR = pkio.py_path('/etc/systemd/system')


#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly, probably

def docker_unit_enable(compt, image, env, cmd, volumes=None, after=None):
    """Must be last call"""
    j2_ctx = pkcollections.Dict(compt.hdb)
    j2_ctx.update(**compt.systemd)
    if 'TZ' not in env:
        # Tested on CentOS 7, and it does have the localtime stat problem
        # https://blog.packagecloud.io/eng/2017/02/21/set-environment-variable-save-thousands-of-system-calls/
        env['TZ'] = ':/etc/localtime'
    j2_ctx.update(
        after=' '.join(after or []),
        service_exec=cmd,
        exports='\n'.join(
            ["export '{}={}'".format(k, env[k]) for k in sorted(env.keys())],
        ),
        image=image + ':' + j2_ctx.channel,
        service=compt.name,
    )
    j2_ctx.volumes = ' '.join(
        ["-v '{}:{}'".format(x, x) for x in [j2_ctx.run_d] + (volumes or [])],
    )
    scripts = ('cmd', 'env', 'remove', 'start', 'stop')
    compt.install_access(mode='700', owner=j2_ctx.run_u)
    compt.install_directory(j2_ctx.run_d)
    compt.install_access(mode='500')
    for s in scripts:
        j2_ctx[s] = j2_ctx.run_d.join(s)
        compt.install_resource('systemd/' + s, j2_ctx, j2_ctx[s])
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # These files should be 400, since there's no value in making them public.
    compt.install_access(mode='444', owner=j2_ctx.root_u)
    compt.install_resource(
        'systemd/service',
        j2_ctx,
        compt.systemd.service_f,
    )
    compt.append_root_bash(
        "rsconf_service_docker_pull '{}' '{}'".format(j2_ctx.service, j2_ctx.image),
    )
    unit_enable(compt)


def docker_unit_prepare(compt):
    """Must be first call"""
    run_d = docker_unit_run_d(compt.hdb, compt.name)
    unit_prepare(compt, run_d)
    compt.systemd.run_d = run_d
    return run_d


def docker_unit_run_d(hdb, unit_name):
    return hdb.host_run_d.join(unit_name)


def unit_enable(compt):
    # rsconf.sh does the actual work of enabling
    # good to have the hook here for clarity
    pass


def unit_prepare(compt, *watch_files):
    """Must be first call"""
    compt.systemd = pkcollections.Dict(
        service_f=_SYSTEMD_DIR.join('{}.service'.format(compt.name)),
    )
    compt.append_root_bash(
        "rsconf_service_prepare '{}' '{}' '{}'".format(
            compt.name,
            compt.systemd.service_f,
            *watch_files
        ),
    )
