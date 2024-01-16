#!/bin/bash
vm_devbox_joeblow_rsconf_component() {
rsconf_service_prepare 'vm_devbox_joeblow' '/etc/systemd/system/vm_devbox_joeblow.service' '/etc/systemd/system/vm_devbox_joeblow.service.d'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/vm_devbox_joeblow/start' '711efae568b1987bbb01c4fd84021914'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/vm_devbox_joeblow.service' '0281d04b4abaec88ab85a6751aa3587f'
}
