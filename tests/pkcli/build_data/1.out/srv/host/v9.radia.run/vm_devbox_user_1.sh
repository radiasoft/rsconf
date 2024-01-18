#!/bin/bash
vm_devbox_user_1_rsconf_component() {
rsconf_service_prepare 'vm_devbox_user_1' '/etc/systemd/system/vm_devbox_user_1.service' '/etc/systemd/system/vm_devbox_user_1.service.d' '/srv/vm_devbox_user_1/start'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/vm_devbox_user_1/start' '98bf9be0ac59d7d6f5764bd8eecfc775'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/vm_devbox_user_1.service' '3c65a04296d9a4798a9d48c4ddeb322c'
}
