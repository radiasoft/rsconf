#!/bin/bash
comsol_rsconf_component() {
rsconf_install_access '700' 'comsol' 'comsol'
rsconf_install_directory '/srv/comsol'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/srv/comsol/db_bkp.sh' '92e4185576f8d627ee05ef6b660668af'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/comsol/db_bkp'
}
