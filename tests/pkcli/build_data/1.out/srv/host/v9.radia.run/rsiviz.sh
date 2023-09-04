#!/bin/bash
rsiviz_rsconf_component() {
rsconf_service_prepare 'rsiviz' '/etc/systemd/system/rsiviz.service' '/etc/systemd/system/rsiviz.service.d' '/srv/rsiviz'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/v9.radia.run.conf' '9e0ce1deb04aaa27a3040b9a354bb66d'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/rsiviz'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/rsiviz/cmd' '70847de8d3358bbb74d57ce10c737acc'
rsconf_install_file '/srv/rsiviz/env' '71d6390229e55ec2e2f66bdf638c8d73'
rsconf_install_file '/srv/rsiviz/remove' 'e6d45cee3bb3361eb08f0708963ca0cc'
rsconf_install_file '/srv/rsiviz/start' '8ed3fcbda952b80bc2dc159316f51f5e'
rsconf_install_file '/srv/rsiviz/stop' '4f07fc3cbe6251f925c60d111ffe7b0f'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/rsiviz.service' 'c31ceff9433c77d00d866e550ad2191a'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/rsiviz:dev' 'rsiviz' 'rsiviz' ''
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/rsiviz/db'
}
