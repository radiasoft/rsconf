#!/bin/bash
celery_sirepo_main() {
    rsconf_require docker rabbitmq
    rsconf_install_access 444 root
    rsconf_install etc/systemd/system/celery_sirepo.service
    rsconf_install_access 700 vagrant
    rsconf_install var/lib/celery_sirepo/ var/lib/sirepo/ var/lib/sirepo/db/ var/lib/sirepo/db/users/
    rsconf_install_access 500
    rsconf_install var/lib/celery_sirepo/{cmd,env,remove,start,stop}
#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly
#TODO(robnagler) only reload if a change, restart if a change
    systemctl daemon-reload
    systemctl start celery_sirepo
    systemctl enable celery_sirepo
}
