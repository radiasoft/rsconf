#!/bin/bash
sirepo_rsconf_component() {
rsconf_service_prepare 'sirepo' '/etc/systemd/system/sirepo.service' '/etc/systemd/system/sirepo.service.d' '/srv/sirepo'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo'
rsconf_install_directory '/srv/sirepo/db'
rsconf_install_directory '/srv/sirepo/db/user'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/sirepo.v4.radia.run.conf' 'ced39a046afab83594da259fb0ea07f7'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo/cmd' 'd0c09ddf98c9bb50a06fc69b0ab2d942'
rsconf_install_file '/srv/sirepo/env' '94f1b85c6a847cca07e8cc77331e273b'
rsconf_install_file '/srv/sirepo/remove' '5b82eb328ed13c904229277b03a1bea7'
rsconf_install_file '/srv/sirepo/start' '7d7b2c8d23e7fa994000836de4023dd9'
rsconf_install_file '/srv/sirepo/stop' 'b3da06740053f873ef5c73fae5dc3e0c'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo.service' 'f4b9810b21098eafe1b73e6e48d0f964'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/sirepo:dev' 'sirepo'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo/db_bkp.sh' '86bdfe43043364479907269cfee18664'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo/db_bkp'
}
