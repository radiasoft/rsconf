#!/bin/bash
vm_devbox_user-1_rsconf_component() {
rsconf_service_prepare 'vm_devbox_user-1' '/etc/systemd/system/vm_devbox_user-1.service' '/etc/systemd/system/vm_devbox_user-1.service.d' '/srv/vm_devbox_user-1/start' '/srv/vm_devbox_user-1/stop'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/vm_devbox_user-1'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/vm_devbox_user-1/start' '0c31920ea4c2b57c901cdeaada039d82'
rsconf_install_file '/srv/vm_devbox_user-1/stop' '94f5e7855deadc753f54580dfad70217'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/vm_devbox_user-1.service' '95beabb09a3e8a9977002d11ae4e47cd'
}
