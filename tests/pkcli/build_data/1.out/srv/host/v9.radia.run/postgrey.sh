#!/bin/bash
postgrey_rsconf_component() {
rsconf_service_prepare 'postgrey' '/etc/systemd/system/postgrey.service' '/etc/systemd/system/postgrey.service.d' '/srv/postgrey' 'bivio-perl-dev.rpm' 'perl-Bivio-dev.rpm'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/postgrey'
rsconf_install_access '755' 'vagrant' 'vagrant'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/postgrey/start' '69a068b5b33614d2132dee497e55aad9'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/postgrey.service' '5ec88c8c7055973fea78a6e45f7c4bb0'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/postgrey'
rsconf_install_directory '/srv/postgrey/db'
rsconf_install_directory '/srv/postgrey/etc'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/postgrey/etc/postgrey_whitelist_recipients' 'fd6333a90b71ea61023e7eafdf90cf94'
rsconf_install_file '/srv/postgrey/etc/postgrey_whitelist_clients.local' '8978955cf2fadfb0e1793fabde3ffb8b'
}
