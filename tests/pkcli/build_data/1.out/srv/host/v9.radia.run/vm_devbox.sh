#!/bin/bash
vm_devbox_rsconf_component() {
vm_devbox_main
}
#!/bin/bash

vm_devbox_main() {
    if vagrant --version > /dev/null 2>&1; then
        return
    fi
    declare p=kernel-devel-$(uname -r)
    if ! yum list "$p" &> /dev/null; then
       install_err "rpm $p not found.
Virtualbox needs the kernel-devel rpm for the host kernel to be installed.
Maybe try updating the kernel? The repos only have kernel-devel for recent versions of the kernel."
    fi
    rsconf_yum_install "$p"
    yum-config-manager --add-repo https://download.virtualbox.org/virtualbox/rpm/el/virtualbox.repo
    yum makecache -y
    rsconf_yum_install VirtualBox-7.0
    yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
    rsconf_yum_install vagrant
}

