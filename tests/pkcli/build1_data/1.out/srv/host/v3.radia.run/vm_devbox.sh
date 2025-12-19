#!/bin/bash
vm_devbox_rsconf_component() {
rsconf_install_access '755' 'root' 'root'
rsconf_install_directory '/srv/libvirt'
rsconf_install_symlink '../../../srv/libvirt' '/var/lib/libvirt'
vm_devbox_main
}
#!/bin/bash

vm_devbox_main() {
    if rpm -q libvirt-devel &> /dev/null; then
        return
    fi
    rsconf_yum_install '@Virtualization Hypervisor' '@Virtualization Tools' '@Development Tools' libvirt-devel
    install_yum_add_repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
    rsconf_yum_install vagrant
    systemctl enable --now libvirtd
    systemctl start libvirtd
    usermod --append --groups libvirt 'vagrant'
}

