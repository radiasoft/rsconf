#!/bin/bash
rsconf_rsconf_component() {
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/v3.radia.run.conf' 'a99754414afc73ce69f5f2adaf389722'
rsconf_install_access '440' 'root' 'nginx'
rsconf_install_file '/etc/nginx/conf.d/rsconf_auth' '27dc8a4ee0c3a27b4b81fd42206307dc'
}
