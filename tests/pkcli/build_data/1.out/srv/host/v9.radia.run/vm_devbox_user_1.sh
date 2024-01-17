#!/bin/bash
vm_devbox_user_1_rsconf_component() {
rsconf_service_prepare 'vm_devbox_user_1' '/etc/systemd/system/vm_devbox_user_1.service' '/etc/systemd/system/vm_devbox_user_1.service.d'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/vm_devbox_user_1/start' '2efa12abc10e3d7c17dd438a20f7e246'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/vm_devbox_user_1.service' '71ffebabf4f912d63c38d4ca357ab79a'
}
