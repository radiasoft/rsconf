#!/bin/bash
vm_devbox_user-1_rsconf_component() {
rsconf_service_prepare 'vm_devbox_user-1' '/etc/systemd/system/vm_devbox_user-1.service' '/etc/systemd/system/vm_devbox_user-1.service.d' '/srv/vm_devbox_user-1/start' '/srv/vm_devbox_user-1/stop'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/vm_devbox_user-1'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/vm_devbox_user-1/start' '081baa61746f4dd28339816bb90453ed'
rsconf_install_file '/srv/vm_devbox_user-1/stop' '94f5e7855deadc753f54580dfad70217'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/vm_devbox_user-1.service' '9bea6d3fc6b169474e19863d1e2da5a3'
}
