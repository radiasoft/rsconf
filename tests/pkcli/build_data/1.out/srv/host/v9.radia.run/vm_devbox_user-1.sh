#!/bin/bash
vm_devbox_user-1_rsconf_component() {
rsconf_service_prepare 'vm_devbox_user-1' '/etc/systemd/system/vm_devbox_user-1.service' '/etc/systemd/system/vm_devbox_user-1.service.d' '/srv/vm_devbox_user-1/start' '/srv/vm_devbox_user-1/stop'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/vm_devbox_user-1'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/vm_devbox_user-1/start' '5dc3180f1dfd32e5d9d15e426928e94a'
rsconf_install_file '/srv/vm_devbox_user-1/stop' '17c8ef8fe2fa06489f4e9cb5869d22b6'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/vm_devbox_user-1.service' '9bea6d3fc6b169474e19863d1e2da5a3'
}
