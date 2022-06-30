#!/bin/bash
bkp_rsconf_component() {
rsconf_service_prepare 'bkp.timer' '/etc/systemd/system/bkp.service' '/etc/systemd/system/bkp.timer' '/srv/bkp'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/bkp/secondary' 'b378d96f4acf76465a22b7f1719645bc'
rsconf_install_file '/srv/bkp/secondary_setup' '9741f7b5e6f288022a8a0a3ce09fed24'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/bkp'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/bkp/start' '845d92f865b14e8d26fb7259608f78ba'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/bkp.timer' '86da49a590261951acbdd39714a10efd'
rsconf_install_file '/etc/systemd/system/bkp.service' '443c9c34df3eddec3268f081e7dead77'
}
