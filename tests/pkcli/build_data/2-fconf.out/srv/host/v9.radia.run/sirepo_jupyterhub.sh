#!/bin/bash
sirepo_jupyterhub_rsconf_component() {
rsconf_service_prepare 'sirepo_jupyterhub' '/etc/systemd/system/sirepo_jupyterhub.service' '/etc/systemd/system/sirepo_jupyterhub.service.d' '/srv/sirepo_jupyterhub'
rsconf_install_access '711' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/jupyterhub'
rsconf_install_access '711' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/jupyterhub/user'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_jupyterhub/conf.py' '7252df400c2f1ebee14af078b2a482ff'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub/docker_tls'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub/docker_tls/v9.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v9.radia.run/cacert.pem' '4b670b08c82a17b5bfbdfc470b444ad5'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v9.radia.run/cert.pem' 'c2e0e0b03583d25969d2d70010c83532'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v9.radia.run/key.pem' '3609cc6739d4773eeea1025a0689c935'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/beamsim-jupyter:dev'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_jupyterhub/cmd' '0528ac7c5915ecc442822798ab8ba5f3'
rsconf_install_file '/srv/sirepo_jupyterhub/env' '97158802a35b528afe338619e2c80042'
rsconf_install_file '/srv/sirepo_jupyterhub/remove' '0405e78988611e08e468f6d19b67118c'
rsconf_install_file '/srv/sirepo_jupyterhub/start' '55f0372dceef059ebc6a013562bfdb37'
rsconf_install_file '/srv/sirepo_jupyterhub/stop' '739860b0b28765ed2fb659615151f7bc'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo_jupyterhub.service' '07db2be4b9dd950013a7cd683b42f981'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/jupyterhub:dev' 'sirepo_jupyterhub'
}