# -*- coding: utf-8 -*-
u"""create systemd files

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

def docker_unit(build_ctx, name, volumes=None, container, after=None):
    from pykern import pkjinja

    radiasoft/sirepo:dev

    '--user=vagrant'

    channel from build context?
    run_d = '/var/lib/' + name

    v=Dict(
        after=after,
    )

    pkjinja.render_resource(
        'docker_unit/service',
        values=env,
        output=where,
    )
