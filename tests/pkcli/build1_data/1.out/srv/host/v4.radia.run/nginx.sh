#!/bin/bash
nginx_rsconf_component() {
rsconf_yum_install nginx
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/star.v4.radia.run.key' '031805b0a7c2e0fd1330b0613f385ede'
rsconf_install_file '/etc/nginx/conf.d/star.v4.radia.run.crt' '19cdea6247d259c6ffb2b36726ea297c'
rsconf_install_file '/etc/nginx/conf.d/www.redirect3.v4.radia.run.key' '41358777f9e5aa8dd6267e40bc165e4e'
rsconf_install_file '/etc/nginx/conf.d/www.redirect3.v4.radia.run.crt' 'bc90227f5d1ee11128b7b29283f789fd'
rsconf_service_prepare 'nginx' '/etc/systemd/system/nginx.service' '/etc/systemd/system/nginx.service.d' '/etc/nginx'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/nginx.conf' '7009fb4c4f580b07a51dc768740c222c'
rsconf_install_access '755' 'root' 'root'
rsconf_install_directory '/srv/www'
rsconf_service_restart_at_end 'nginx'
}
