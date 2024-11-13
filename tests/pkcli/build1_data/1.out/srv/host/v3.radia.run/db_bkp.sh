#!/bin/bash
db_bkp_rsconf_component() {
rsconf_service_prepare 'db_bkp.timer' '/etc/systemd/system/db_bkp.service' '/etc/systemd/system/db_bkp.timer' '/srv/db_bkp'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/db_bkp'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/db_bkp/start' 'ede6d1b77f171c00358e47296b67c19f'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/db_bkp.timer' '64cdcbfab454f653ae9eb19bb0e138a3'
rsconf_install_file '/etc/systemd/system/db_bkp.service' '3fae29a217fc19782485d59cb3d5a732'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/db_bkp/run' '07b2df16d25e42b467105336f512f8f0'
}
