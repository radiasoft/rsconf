# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function


def rsconf_build(build_ctx):
    build_ctx.install_file(
        # from where?
        ['etc/systemd/system/sirepo.service'],
        mode='444',
        owner='root',
    )
    build_ctx.install_file(
        ['var/lib/sirepo/cmd',
        'var/lib/sirepo/env',
        'var/lib/sirepo/remove',
        'var/lib/sirepo/start',
        'var/lib/sirepo/stop'],
        mode=500,
        owner='vagrant',
    )
    build_ctx.install_dir(
        ['var/lib/sirepo/db/user'],
        mode='700',
        owner='vagrant',
    )
    build_ctx.install_file(
#create if does not already exist in secret
        ['var/lib/sirepo/db/beaker_secret'],
        mode='400',
        owner='vagrant',
    )
#If anything changes, restart service, otherwise just start
    systemctl daemon-reload
    systemctl start sirepo
    systemctl enable sirepo

#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly
#TODO(robnagler) only reload if a change, restart if a change
