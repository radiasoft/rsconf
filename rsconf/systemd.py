# -*- coding: utf-8 -*-
u"""create systemd files

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig
from pykern import pkio
import types


_SYSTEMD_DIR = pkio.py_path('/etc/systemd/system')


#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly, probably

def docker_unit_enable(compt, image, cmd, env=None, volumes=None, after=None, run_u=None, ports=None):
    """Must be last call"""
    from rsconf.component import docker_registry

    j2_ctx = compt.hdb.j2_ctx_copy()
    v = pkcollections.Dict(compt.systemd)
    if env is None:
        env = pkcollections.Dict()
    if 'TZ' not in env:
        # Tested on CentOS 7, and it does have the localtime stat problem
        # https://blog.packagecloud.io/eng/2017/02/21/set-environment-variable-save-thousands-of-system-calls/
        env['TZ'] = ':/etc/localtime'
    image = docker_registry.absolute_image(j2_ctx, image)
    v.update(
        after=' '.join(after or []),
        service_exec=cmd,
        exports='\n'.join(
            ["export '{}={}'".format(k, env[k]) for k in sorted(env.keys())],
        ),
        image=image,
        run_u=run_u or j2_ctx.rsconf_db.run_u,
    )
    v.volumes = ' '.join(
        ["-v '{}'".format(_colon_arg(x)) for x in [v.run_d] + (volumes or [])],
    )
    v.network = ' '.join(
        ["-p '{}'".format(_colon_arg(x)) for x in (ports or [])],
    )
    if not v.network:
        v.network = '--network=host'
    scripts = ('cmd', 'env', 'remove', 'start', 'stop')
    compt.install_access(mode='700', owner=v.run_u)
    compt.install_directory(v.run_d)
    compt.install_access(mode='500')
    for s in scripts:
        v[s] = v.run_d.join(s)
    if not cmd:
        v.cmd = ''
    j2_ctx.setdefault('systemd', pkcollections.Dict()).update(v)
    for s in scripts:
        if v[s]:
            compt.install_resource('systemd/' + s, j2_ctx, v[s])
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # These files should be 400, since there's no value in making them public.
    compt.install_access(mode='444', owner=j2_ctx.rsconf_db.root_u)
    compt.install_resource(
        'systemd/service',
        j2_ctx,
        v.service_f,
    )
    compt.append_root_bash(
        "rsconf_service_docker_pull '{}' '{}'".format(v.image, v.service_name),
    )
    unit_enable(compt)


def docker_unit_prepare(compt):
    """Must be first call"""
    run_d = unit_run_d(compt.hdb, compt.name)
    unit_prepare(compt, run_d)
    compt.systemd.run_d = run_d
    return run_d


def timer_enable(compt, j2_ctx, on_calendar, timer_exec):
    z = j2_ctx.systemd
    compt.install_access(mode='700', owner=j2_ctx.rsconf_db.root_u)
    compt.install_directory(z.run_d)
    compt.install_access(mode='444')
    z.on_calendar = on_calendar
    z.timer_exec = timer_exec
    compt.install_resource(
        'systemd/timer',
        j2_ctx,
        z.timer_f,
    )
    compt.install_resource(
        'systemd/timer_service',
        j2_ctx,
        z.service_f,
    )
    compt.install_access(mode='500')
    compt.install_resource(
        'systemd/timer_start',
        j2_ctx,
        z.timer_start_f,
    )
    unit_enable(compt)


def timer_prepare(compt, j2_ctx, *watch_files):
    """Must be first call"""
    n = compt.name
    tn = n + '.timer'
    run_d = unit_run_d(j2_ctx, n)
    j2_ctx.systemd = pkcollections.Dict(
        run_d=run_d,
        service_f=_SYSTEMD_DIR.join(n + '.service'),
        service_name=n,
        timer_f=_SYSTEMD_DIR.join(tn),
        timer_name=tn,
        timer_start_f=run_d.join('start'),
    )
    compt.service_prepare(
        (j2_ctx.systemd.service_f, j2_ctx.systemd.timer_f, run_d) + watch_files,
        name=tn,
    )
    return run_d


def unit_enable(compt):
    # rsconf.sh does the actual work of enabling
    # good to have the hook here for clarity
    pass


def unit_prepare(compt, *watch_files):
    """Must be first call"""
    compt.systemd = pkcollections.Dict(
        service_name=compt.name,
        service_f=_SYSTEMD_DIR.join('{}.service'.format(compt.name)),
    )
    compt.service_prepare((compt.systemd.service_f,) + watch_files)


def unit_run_d(hdb, unit_name):
    return hdb.rsconf_db.host_run_d.join(unit_name)


def _colon_arg(v):
    if not isinstance(v, (tuple, list)):
        v = (v, v)
    return '{}:{}'.format(*v)
