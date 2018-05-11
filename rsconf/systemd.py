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

def custom_unit_enable(compt, j2_ctx, start='start', reload=None, stop=None, after=None, run_u=None, resource_d=None, run_d_mode='700', run_group=None):
    """Must be last call"""
    if not resource_d:
        resource_d = compt.name
    z = j2_ctx.systemd
    z.update(
        after=' '.join(after or []),
        reload=reload,
        run_u=run_u or j2_ctx.rsconf_db.run_u,
        start=start,
        stop=stop,
    )
    z.run_group = run_group or z.run_u
    scripts = ('reload', 'start', 'stop')
    compt.install_access(mode=run_d_mode, owner=z.run_u, group=z.run_group)
    compt.install_directory(z.run_d)
    # pid_file has to be in a public directory that is writeable by run_u
    # "PID file /srv/petshop/petshop.pid not readable (yet?) after start."
    compt.install_access(mode='755')
    z.runtime_d = pkio.py_path('/run').join(z.service_name)
    # systemd creates RuntimeDirectory in /run see custom_unit.servicea
    z.pid_file = z.runtime_d.join(z.service_name + '.pid')
    compt.install_access(mode='500')
    for s in scripts:
        if z[s]:
            z[s] = z.run_d.join(s)
            compt.install_resource(
                resource_d + '/' + s + '.sh',
                j2_ctx,
                z[s],
            )
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # These files should be 400, since there's no value in making them public.
    compt.install_access(mode='444', owner=j2_ctx.rsconf_db.root_u)
    compt.install_resource(
        'systemd/custom_unit',
        j2_ctx,
        z.service_f,
    )
    unit_enable(compt, j2_ctx)


def custom_unit_prepare(compt, j2_ctx, watch_files=()):
    """Must be first call"""
    run_d = unit_run_d(j2_ctx, compt.name)
    unit_prepare(compt, j2_ctx, [run_d] + list(watch_files))
    j2_ctx.systemd.run_d = run_d
    j2_ctx.systemd.is_timer = False
    return run_d


def docker_unit_enable(compt, j2_ctx, image, cmd, env=None, volumes=None, after=None, run_u=None, ports=None, extra_run_flags=None):
    """Must be last call"""
    from rsconf.component import docker_registry

    z = j2_ctx.systemd
    if env is None:
        env = pkcollections.Dict()
    if 'TZ' not in env:
        # Tested on CentOS 7, and it does have the localtime stat problem
        # https://blog.packagecloud.io/eng/2017/02/21/set-environment-variable-save-thousands-of-system-calls/
        env['TZ'] = ':/etc/localtime'
    image = docker_registry.absolute_image(j2_ctx, image)
    z.update(
        after=' '.join(after or []),
        extra_run_flags=' '.join("'{}'".format(f) for f in extra_run_flags) if extra_run_flags else '',
        service_exec=cmd,
        exports='\n'.join(
            ["export '{}={}'".format(k, env[k]) for k in sorted(env.keys())],
        ),
        image=image,
        run_u=run_u or j2_ctx.rsconf_db.run_u,
    )
    z.volumes = ' '.join(
        ["-v '{}'".format(_colon_arg(x)) for x in [z.run_d] + (volumes or [])],
    )
    z.network = ' '.join(
        ["-p '{}'".format(_colon_arg(x)) for x in (ports or [])],
    )
    if not z.network:
        z.network = '--network=host'
    scripts = ('cmd', 'env', 'remove', 'start', 'stop')
    compt.install_access(mode='700', owner=z.run_u)
    compt.install_directory(z.run_d)
    compt.install_access(mode='500')
    for s in scripts:
        z[s] = z.run_d.join(s)
    if not cmd:
        z.cmd = ''
    for s in scripts:
        if z[s]:
            compt.install_resource('systemd/docker_' + s, j2_ctx, z[s])
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # These files should be 400, since there's no value in making them public.
    compt.install_access(mode='444', owner=j2_ctx.rsconf_db.root_u)
    if z.is_timer:
        compt.install_resource(
            'systemd/timer_unit',
            j2_ctx,
            z.timer_f,
        )
    compt.install_resource(
        'systemd/docker_unit',
        j2_ctx,
        z.service_f,
    )
    compt.append_root_bash(
        "rsconf_service_docker_pull '{}' '{}'".format(z.image, z.service_name),
    )
    unit_enable(compt, j2_ctx)


def docker_unit_prepare(compt, j2_ctx, watch_files=()):
    """Must be first call"""
    return custom_unit_prepare(compt, j2_ctx, watch_files)


def timer_enable(compt, j2_ctx, cmd, run_u=None):
    z = j2_ctx.systemd
    z.run_u = run_u or j2_ctx.rsconf_db.run_u
    compt.install_access(mode='700', owner=z.run_u)
    compt.install_directory(z.run_d)
    # required by systemd
    z.timer_exec = cmd
    compt.install_access(mode='500')
    compt.install_resource(
        'systemd/timer_start',
        j2_ctx,
        z.timer_start_f,
    )
    compt.install_access(mode='444', owner=j2_ctx.rsconf_db.root_u)
    compt.install_resource(
        'systemd/timer_unit',
        j2_ctx,
        z.timer_f,
    )
    compt.install_resource(
        'systemd/timer_unit_service',
        j2_ctx,
        z.service_f,
    )
    unit_enable(compt, j2_ctx)


def timer_prepare(compt, j2_ctx, on_calendar, watch_files=(), service_name=None):
    """Must be first call"""
    n = service_name or compt.name
    tn = n + '.timer'
    run_d = unit_run_d(j2_ctx, n)
    j2_ctx.systemd = pkcollections.Dict(
        is_timer=True,
        on_calendar=on_calendar,
        run_d=run_d,
        service_f=_SYSTEMD_DIR.join(n + '.service'),
        service_name=n,
        timer_f=_SYSTEMD_DIR.join(tn),
        timer_name=tn,
        timer_start_f=run_d.join('start'),
    )
    compt.service_prepare(
        [j2_ctx.systemd.service_f, j2_ctx.systemd.timer_f, run_d] + list(watch_files),
        name=tn,
    )
    return run_d


def unit_enable(compt, j2_ctx):
    # rsconf.sh does the actual work of enabling
    # good to have the hook here for clarity
    pass


def unit_prepare(compt, j2_ctx, watch_files=()):
    """Must be first call"""
    j2_ctx.systemd = pkcollections.Dict(
        service_name=compt.name,
        service_f=_SYSTEMD_DIR.join('{}.service'.format(compt.name)),
    )
    compt.service_prepare([j2_ctx.systemd.service_f] + list(watch_files))


def unit_run_d(j2_ctx, unit_name):
    return j2_ctx.rsconf_db.host_run_d.join(unit_name)


def _colon_arg(v):
    if not isinstance(v, (tuple, list)):
        v = (v, v)
    return '{}:{}'.format(*v)
