#!/bin/bash
vm_devbox_rsconf_component() {
vm_devbox_main
}
#!/bin/bash

vm_devbox_main() {
    if rpm -q libvirt-devel &> /dev/null 2>&1; then
        return
    fi
    yum-config-manager --set-enabled crb
    rsconf_yum_install '@Virtualization Hypervisor' '@Virtualization Tools' '@Development Tools' libvirt-devel
    yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
    rsconf_yum_install vagrant
    systemctl enable --now libvirtd
    systemctl start libvirtd
    usermod --append --groups libvirt 'vagrant'
}

