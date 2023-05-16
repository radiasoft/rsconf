#!/bin/bash
nginx_rsconf_component() {
rsconf_yum_install nginx
rsconf_install_access '400' 'root' 'root'
rsconf_service_prepare 'nginx' '/etc/systemd/system/nginx.service' '/etc/systemd/system/nginx.service.d' '/etc/nginx'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/v9.radia.run.key' 'fe22a3a98b83d3cd8d48eb5ccda07d60'
rsconf_install_file '/etc/nginx/conf.d/v9.radia.run.crt' 'a6d3bba40727a12f03b1f44727bb98be'
rsconf_install_file '/etc/nginx/nginx.conf' '7ed366def6fee2bd4685738829db273f'
rsconf_install_access '755' 'root' 'root'
rsconf_install_directory '/srv/www'
rsconf_service_restart_at_end 'nginx'
}
