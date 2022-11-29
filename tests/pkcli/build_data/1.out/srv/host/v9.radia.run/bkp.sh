#!/bin/bash
bkp_rsconf_component() {
rsconf_service_prepare 'bkp.timer' '/etc/systemd/system/bkp.service' '/etc/systemd/system/bkp.timer' '/srv/bkp'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/bkp/secondary' 'f91c10fc0fdfe67360067343a2577c1b'
rsconf_install_file '/srv/bkp/secondary_setup' '84b40460f8374ccbde4c353cc301f5fc'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/bkp'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/bkp/start' '845d92f865b14e8d26fb7259608f78ba'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/bkp.timer' '97d463b79906d1e9b794937d3a9c4993'
rsconf_install_file '/etc/systemd/system/bkp.service' '443c9c34df3eddec3268f081e7dead77'
}
