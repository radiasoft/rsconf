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
rsconf_install_file '/srv/sirepo_jupyterhub/conf.py' '7d8e2cabf15913255261ef0436fef3f3'
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
rsconf_install_file '/srv/sirepo_jupyterhub/env' '1d6ee44c5cc0ebf9c2593aa7c86e7938'
rsconf_install_file '/srv/sirepo_jupyterhub/remove' '3c770851c99f7d752b07151b19e5a714'
rsconf_install_file '/srv/sirepo_jupyterhub/start' '11ffa5be350d0958a30eadfcfae3bd97'
rsconf_install_file '/srv/sirepo_jupyterhub/stop' 'af5da1fe24d5f3275dc87735659461ff'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo_jupyterhub.service' '84f6e6fa42dcb7f829ead0f207eac8a4'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/jupyterhub:dev' 'sirepo_jupyterhub' 'sirepo_jupyterhub' ''
}
