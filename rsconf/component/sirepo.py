# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function


class T(component.T):
    def internal_build(self):
        from rsconf import systemd

        self.docker_image =
        self.buildt.require_component('docker', 'rabbitmq', 'celery_sirepo', 'nginx')
        run_d = systemd.docker_unit_run_d(self)
        db_d = run_d.join('db')
        env=pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=self.buildt.host.channel,
            PYKERN_PKDEBUG_CONTROL='sirepo',
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
            SIREPO_MPI_CORES=self.buildt.host.mpi_cores,
            SIREPO_PKCLI_SERVICE_IP=0.0.0.0,
            SIREPO_PKCLI_SERVICE_PORT=self.buildt.host.sirepo_port,
            SIREPO_PKCLI_SERVICE_PROCESSES=1,
            SIREPO_PKCLI_SERVICE_RUN_DIR=run_d,
            SIREPO_PKCLI_SERVICE_THREADS=20,
            SIREPO_SERVER_BEAKER_SESSION_KEY='sirepo_{}'.format(self.buildt.host.channel),
            SIREPO_SERVER_BEAKER_SESSION_SECRET=db_d.join('beaker_secret'),
            SIREPO_CELERY_TASKS_BROKER_URL=self.buildt.host.amqp,
            SIREPO_SERVER_DB_DIR=db_d,
            SIREPO_SERVER_JOB_QUEUE=Celery,
        )
        k = self.host.get('oauth_github')
        if k:
            env.update(
                SIREPO_OAUTH_GITHUB_KEY=k.key,
                SIREPO_OAUTH_GITHUB_SECRET=k.secret,
                SIREPO_SERVER_OAUTH_LOGIN=1,
            )
        systemd.docker_unit(
            self,
            run_d=run_d,
            env=env,
            image='radiasoft/sirepo',
            volumes=[],
            after=['docker.service', 'celery_sirepo.service'],
        )
        self.create secret
            two alphas(?), not really, may have different os, no that is a tree
            alpha.yml
            alpha-sirepo.yml
            v4.bivio.biz.yml
            v4.bivio.biz-sshd-host-key - add to backup machine
            look for a secret by name alpha-sirepo-beaker_secret
            how to generate(?) - provided by caller
            if the secret is not defined, it is generated
            secrets can be stored in files (key, private, crt)
            get secret by (system, component, host)
               channel has a single secret for sirepo (always a component)
            each component on a host has a channel, secret is stored with that

        self.install_file(
    #create if does not already exist in secret
            'var/lib/sirepo/db/beaker_secret',
            mode='400',
            owner='vagrant',
        )
    #If anything changes, restart service, otherwise just start
        rabbitmq depends on docker
        sirepo depends on celery_sirepo
        nginx server depends on sirepo
        those relationships are in "after"
        but also need to be elsewhere.
        systemctl daemon-reload
        systemctl start sirepo
        systemctl enable sirepo

#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly
#TODO(robnagler) only reload if a change, restart if a change
