# -*- coding: utf-8 -*-
u"""create systemd files

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkio

SYSTEMD_DIR = pkio.py_path('/etc/systemd/system')


def docker_unit_run_d(compt):
    return compt.buildt.dbt.guest_root_d.join(compt.name)


def docker_unit(compt, run_d, image, volumes, env, after=None):
    from pykern import pkcollections

    run_user = compt.buildt.run_user
    values = pkcollections.Dict(
        name=compt.name,
        run_user=run_user,
    )

    values.exports = '\n'.join(
        ["export '{}={}'".format(k, env[k]) for k in sorted(env.keys())],
    )

    compt.install_access(mode=500, owner=run_user)
    scripts = ('cmd', 'env', 'remove', 'start', 'stop')
    for s in scripts:
        values[s] = run_d.join(s)
        compt.install_resource('docker_unit/' + s, values, value[s])

    volumes.append(run_d)
    values.volumes = ' '.join(["-v '{}:{}'".format(x, x) for x in volumes])
    values.image = image + ':' + compt.buildt.host.channel
    compt.install_access(mode=444, owner=compt.buildt.root_user)
    compt.install_resource(
        'docker_unit/service',
        values=values,
        SYSTEMD_DIR.join('{}.service'.format(compt.name))
    )
after
required_by

    compt.install_file(
        [run_d + x for
        run_d + cmd,
            mode=500,
            owner='vagrant',
        )
        self.install_dir(
            'var/lib/sirepo/db/user',
            mode='700',
            owner='vagrant',
        )

radiasoft/sirepo:dev
-v /var/lib/sirepo:/var/lib/sirepo

    pkcollections.Dict()

    # current component
    buildt.install_file(
        # from where?
        ['etc/systemd/system/sirepo.service'],
        mode='444',
        owner='root',
    )


    radiasoft/sirepo:dev

    '--user=vagrant'

    channel from build context?
    run_d = '/var/lib/' + name

    v=Dict(
        after=after,
    )
    return run_d
