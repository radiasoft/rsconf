#!/bin/bash
script_rsconf_component() {
echo hello

rsconf_service_prepare 'every_five.timer' '/etc/systemd/system/every_five.service' '/etc/systemd/system/every_five.timer' '/srv/every_five'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/every_five/run' '99fa414cbe03e1be17e1512c93caa413'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/every_five'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/every_five/start' '4ec245b018ccd9d3439958d81bf70acf'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/every_five.timer' 'd9cf11885ef351c6de1459426f91c654'
rsconf_install_file '/etc/systemd/system/every_five.service' '8ba4919aed381df75e79c8780bb1acf6'
}
