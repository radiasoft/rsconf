#!/bin/bash
rabbitmq_main() {
    rsconf_require docker
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # I would want these files to be 400, since there's no value in making them
    # public. The machines are inaccessiable to anybody who doesn't have root access.
    rsconf_install_access 444 root
    rsconf_install etc/systemd/system/rabbitmq.service
    rsconf_install_access 700 vagrant
    rsconf_install var/lib/rabbitmq/ var/lib/rabbitmq/log/ var/lib/rabbitmq/mnesia/
    rsconf_install_access 400
    if ! cmp -s /etc/skel/.bashrc /var/lib/rabbitmq/.bashrc >& /dev/null; then
        cp /etc/skel/.bashrc /var/lib/rabbitmq/.bashrc
        rsconf_install_chxxx /var/lib/rabbitmq/.bashrc
    fi
    rsconf_install var/lib/rabbitmq/{enabled_plugins,rabbitmq.config}
    rsconf_install_access 500
    rsconf_install var/lib/rabbitmq/{cmd,env,remove,start,stop}
#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly
#TODO(robnagler) only reload if a change, restart if a change
    systemctl daemon-reload
    systemctl start rabbitmq
    systemctl enable rabbitmq
}
