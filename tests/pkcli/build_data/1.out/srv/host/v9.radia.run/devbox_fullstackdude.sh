#!/bin/bash
devbox_fullstackdude_rsconf_component() {
rsconf_service_prepare 'devbox_fullstackdude' '/etc/systemd/system/devbox_fullstackdude.service' '/etc/systemd/system/devbox_fullstackdude.service.d' '/srv/devbox_fullstackdude' '/srv/devbox_fullstackdude/sshd'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/devbox_fullstackdude'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/devbox_fullstackdude/cmd' 'cdcf85170cfe88770e11b1fdb2062550'
rsconf_install_file '/srv/devbox_fullstackdude/env' '22e03a134cc868bb12094d8dc118a6c4'
rsconf_install_file '/srv/devbox_fullstackdude/remove' '2e3f05447c3a666355e47923fc17dc79'
rsconf_install_file '/srv/devbox_fullstackdude/start' '8531dfcc84910bb4e094d7fea634a1d8'
rsconf_install_file '/srv/devbox_fullstackdude/stop' 'b9d49c0e7995043a88d9602b0cf6e284'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/devbox_fullstackdude.service' 'e8e49c2404fb1c49825f03be1ab333fe'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/beamsim-jupyter:dev' 'devbox_fullstackdude' 'devbox_fullstackdude' ''
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/devbox_fullstackdude/jupyter'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/devbox_fullstackdude/src'
rsconf_install_directory '/srv/devbox_fullstackdude/src/biviosoftware'
rsconf_install_directory '/srv/devbox_fullstackdude/src/biviosoftware/home-env'
rsconf_clone_repo https://github.com/biviosoftware/home-env.git /srv/devbox_fullstackdude/src/biviosoftware/home-env vagrant
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/devbox_fullstackdude/sshd'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/devbox_fullstackdude'
rsconf_install_access '600' 'vagrant' 'vagrant'
rsconf_install_ensure_file_exists '/srv/devbox_fullstackdude/jupyter/bashrc'
rsconf_edit_no_change_res=0 rsconf_append $'/srv/devbox_fullstackdude/jupyter/bashrc' $'export SIREPO_FEATURE_CONFIG_PACKAGE_PATH=\'sirepo\''
rsconf_edit_no_change_res=0 rsconf_append $'/srv/devbox_fullstackdude/jupyter/bashrc' $'export SIREPO_FEATURE_CONFIG_SIM_TYPES=\'elegant:srw\''
rsconf_edit_no_change_res=0 rsconf_append $'/srv/devbox_fullstackdude/jupyter/bashrc' $'export SIREPO_PKCLI_SERVICE_PORT=\'3201\''
rsconf_edit_no_change_res=0 rsconf_append $'/srv/devbox_fullstackdude/jupyter/bashrc' $'export SIREPO_PKCLI_JOB_SUPERVISOR_PORT=\'3301\''
rsconf_edit_no_change_res=0 rsconf_append $'/srv/devbox_fullstackdude/jupyter/bashrc' $'export SIREPO_JOB_DRIVER_LOCAL_SUPERVISOR_URI=\'http://127.0.0.1:3301\''
rsconf_edit_no_change_res=0 rsconf_append $'/srv/devbox_fullstackdude/jupyter/bashrc' $'export SIREPO_JOB_API_SUPERVISOR_URI=\'http://127.0.0.1:3301\''
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/devbox_fullstackdude/sshd/sshd_config' 'f432400feaa235ff0e4675c059e453de'
rsconf_install_file '/srv/devbox_fullstackdude/sshd/host_key' '51239a03b3421de7b20b9fb5f8c0f632'
rsconf_install_file '/srv/devbox_fullstackdude/sshd/identity.pub' 'c3d2bac784399f08153d897c5d38dd84'
}
