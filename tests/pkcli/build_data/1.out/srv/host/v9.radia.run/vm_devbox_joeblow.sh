#!/bin/bash
vm_devbox_joeblow_rsconf_component() {
rsconf_service_prepare 'vm_devbox_joeblow' '/etc/systemd/system/vm_devbox_joeblow.service' '/etc/systemd/system/vm_devbox_joeblow.service.d'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/vm_devbox_joeblow/v'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/vm_devbox_joeblow/start' 'e7f1bf9a7c05ed3fdfcf593137bc6d47'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/vm_devbox_joeblow.service' '0281d04b4abaec88ab85a6751aa3587f'
}
