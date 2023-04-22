#!/bin/bash
sirepo_rsconf_component() {
rsconf_service_prepare 'sirepo' '/etc/systemd/system/sirepo.service' '/etc/systemd/system/sirepo.service.d' '/srv/sirepo'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo'
rsconf_install_directory '/srv/sirepo/db'
rsconf_install_directory '/srv/sirepo/db/user'
rsconf_install_directory '/srv/sirepo/db/proprietary_code'
rsconf_install_directory '/srv/sirepo/db/proprietary_code/myapp'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo/db/proprietary_code/myapp/myapp.tar.gz' 'd34fdd385754905a66a7661d5abf1192'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/sirepo.v4.radia.run.conf' '462f755a8939749b16384e21aa64e4c3'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo/cmd' 'd0c09ddf98c9bb50a06fc69b0ab2d942'
rsconf_install_file '/srv/sirepo/env' '05f5a0c5402272c13bbac6dc96a647b3'
rsconf_install_file '/srv/sirepo/remove' '5b82eb328ed13c904229277b03a1bea7'
rsconf_install_file '/srv/sirepo/start' '6804e17572ec5993d31667e2f281bdb1'
rsconf_install_file '/srv/sirepo/stop' 'b3da06740053f873ef5c73fae5dc3e0c'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo.service' 'f4b9810b21098eafe1b73e6e48d0f964'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/sirepo:dev' 'sirepo' 'sirepo' ''
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo/db_bkp.sh' '86bdfe43043364479907269cfee18664'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo/db_bkp'
}
