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
rsconf_install_file '/srv/jupyterhub/remove' '7e85c7682a21bd7dd7c8c16edf89a36f'
rsconf_install_file '/srv/jupyterhub/start' 'bdc43f841085efa18077eecd3b6e3685'
rsconf_install_file '/srv/jupyterhub/stop' '27680beab256838b6f52d50291d3a5bd'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/jupyterhub.service' 'cb213f604499026450bc1646a91868ae'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/jupyterhub:dev' 'jupyterhub' 'jupyterhub' ''
}
