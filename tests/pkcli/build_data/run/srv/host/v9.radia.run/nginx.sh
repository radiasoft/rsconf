#!/bin/bash
nginx_rsconf_component() {
rsconf_yum_install nginx
rsconf_install_access '400' 'root' 'root'
rsconf_service_prepare 'nginx' '/etc/systemd/system/nginx.service' '/etc/systemd/system/nginx.service.d' '/etc/nginx'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/v9.radia.run.key' '79217e58aceeddf749b58dac0c9c2c84'
rsconf_install_file '/etc/nginx/conf.d/v9.radia.run.crt' 'a2fa2f430397fa91705e4e07ce23e60b'
rsconf_install_file '/etc/nginx/nginx.conf' '6b4ff2b1e619ddb22fb7e63b68c78d77'
rsconf_service_restart_at_end 'nginx'
}
