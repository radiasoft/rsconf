#!/bin/bash

base_os_main() {
    local i=$(sysctl -n net.ipv6.conf.all.disable_ipv6)
    rsconf_install_access 400 root root
    rsconf_install etc/sysctl.d/60-rsconf-base.conf 400
    sysctl -p --system
    if (( $i == 0 )); then
        # https://access.redhat.com/solutions/8709
        # Must be done first time
        install_info 'Rebuilding initrd to disable ipv6'
        # Not bothering with backup, because this only happens once after fresh
        # restart.
        dracut -f
    fi
    yum --enablerepo=extras install -y -q epel-release
    local x=(
        bind-utils
        emacs-nox
        git
        patch
        perl
        strace
        unzip
        wget
    )
    yum install -y -q "${x[@]}"
    # https://access.redhat.com/solutions/8709
    # breaks SSH Xforwarding unless AddressFamily inet is set in sshd_config
    # idempotent so ok to repeat and the file might get updated with a new release.
    perl -pi -e 's{^#AddressFamily any}{AddressFamily inet}' /etc/ssh/sshd_config
#TODO(robnagler) reboot?
}
