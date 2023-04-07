#!/bin/bash
jupyterhub_rsconf_component() {
rsconf_service_prepare 'jupyterhub' '/etc/systemd/system/jupyterhub.service' '/etc/systemd/system/jupyterhub.service.d' '/srv/jupyterhub'
rsconf_install_access '711' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/jupyterhub'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/jupyterhub/user'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/jupyterhub/conf.py' '2bbc0bfc0eaa86b6fea974e6c9f0aebf'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/jupyterhub/docker_tls'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/jupyterhub/docker_tls/v9.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/jupyterhub/docker_tls/v9.radia.run/cacert.pem' '4b670b08c82a17b5bfbdfc470b444ad5'
rsconf_install_file '/srv/jupyterhub/docker_tls/v9.radia.run/cert.pem' '490114bf5651cf7b0799924ab1df3a8c'
rsconf_install_file '/srv/jupyterhub/docker_tls/v9.radia.run/key.pem' '7a340105c846fcf0d6aa2cc4a5e5174a'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/jupyterhub'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/jupyterhub/cmd' '22701a5208906e140fc0e2a71800be0a'
rsconf_install_file '/srv/jupyterhub/env' '22e03a134cc868bb12094d8dc118a6c4'
rsconf_install_file '/srv/jupyterhub/remove' 'fe59b6971e147bd641a8ec95d2f021a7'
rsconf_install_file '/srv/jupyterhub/start' '91bcfd89a85275de9258c8e199ed29ec'
rsconf_install_file '/srv/jupyterhub/stop' '52cdba91c58d9979b5ac5adf71887ce5'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/jupyterhub.service' 'cb213f604499026450bc1646a91868ae'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/jupyterhub:dev' 'jupyterhub'
}
