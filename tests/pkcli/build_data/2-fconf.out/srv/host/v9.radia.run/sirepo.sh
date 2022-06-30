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
rsconf_install_file '/srv/sirepo/db/proprietary_code/myapp/myapp.tar.gz' '4d1f6511bcdef94400456f1d227f2b08'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/sirepo.v4.radia.run.conf' 'c7172826d9a27a60a2ed66702a0e0396'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo/cmd' 'd0c09ddf98c9bb50a06fc69b0ab2d942'
rsconf_install_file '/srv/sirepo/env' '9d8b16cd02a61fae568920437fec4ee4'
rsconf_install_file '/srv/sirepo/remove' 'da9bc715b4578d0cbedb66e846d9d988'
rsconf_install_file '/srv/sirepo/start' 'fb7420e1b85e8bc715f899c4c631816e'
rsconf_install_file '/srv/sirepo/stop' '356c4176ab3adc78391f212b5dbc6907'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo.service' '89b2cea14ac3147534e5cd55c41eb080'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/sirepo:dev' 'sirepo'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo/db_bkp.sh' '86bdfe43043364479907269cfee18664'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo/db_bkp'
}
