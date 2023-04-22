#!/bin/bash
nginx_rsconf_component() {
rsconf_yum_install nginx
rsconf_install_access '400' 'root' 'root'
rsconf_service_prepare 'nginx' '/etc/systemd/system/nginx.service' '/etc/systemd/system/nginx.service.d' '/etc/nginx'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/v3.radia.run.key' 'b98bb61f3b76969ee1a259d5a1afd5f1'
rsconf_install_file '/etc/nginx/conf.d/v3.radia.run.crt' '71151618f3ca16bad2d73ef5a6683c1c'
rsconf_install_file '/etc/nginx/nginx.conf' 'acb1cd31b72d4aa9678081779758c65b'
rsconf_install_access '755' 'root' 'root'
rsconf_install_directory '/srv/www'
rsconf_service_restart_at_end 'nginx'
}
