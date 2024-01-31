#!/bin/bash
vm_devbox_user-1_rsconf_component() {
rsconf_service_prepare 'vm_devbox_user-1' '/etc/systemd/system/vm_devbox_user-1.service' '/etc/systemd/system/vm_devbox_user-1.service.d' '/srv/vm_devbox_user-1/start'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/vm_devbox_user-1'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/vm_devbox_user-1/start' '46de8c2ad8e5fcb3d074110e25d70136'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/vm_devbox_user-1.service' '1bd0318206a0d747ce7ab0247d1d6b39'
}
