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
rsconf_install_file '/srv/sirepo_jupyterhub/conf.py' '0486417406c617838f9a4a0cd4757c9e'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub/docker_tls'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub/docker_tls/v6.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v6.radia.run/cacert.pem' 'c7b7e3368b45d1bec5986935b7e7dab6'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v6.radia.run/cert.pem' 'fc77df0c4b3f87d927c73c03921f35da'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v6.radia.run/key.pem' 'bb75b7e15732fd0db337c5cce88b260a'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub/docker_tls/v5.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v5.radia.run/cacert.pem' '6decfd9aa3b78cb106c38a000343fd62'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v5.radia.run/cert.pem' '28d983883720818657c8feaa4e140397'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v5.radia.run/key.pem' 'd3f7a219e7af645903d61380afc71b96'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub/docker_tls/v4.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v4.radia.run/cacert.pem' '821c1182ee9529bfdae5bbd509fe9299'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v4.radia.run/cert.pem' '6729ca250173c516d3ba332c24c69657'
rsconf_install_file '/srv/sirepo_jupyterhub/docker_tls/v4.radia.run/key.pem' '981c5be64e973c992224638fc693ee1b'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/beamsim-jupyter:dev'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_jupyterhub'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_jupyterhub/cmd' '0528ac7c5915ecc442822798ab8ba5f3'
rsconf_install_file '/srv/sirepo_jupyterhub/env' '9861492c9e477e498ff6c2b16511d90a'
rsconf_install_file '/srv/sirepo_jupyterhub/remove' '3c770851c99f7d752b07151b19e5a714'
rsconf_install_file '/srv/sirepo_jupyterhub/start' '737e537de0212793b3fbc9cfa372747a'
rsconf_install_file '/srv/sirepo_jupyterhub/stop' 'af5da1fe24d5f3275dc87735659461ff'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo_jupyterhub.service' '84f6e6fa42dcb7f829ead0f207eac8a4'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/jupyterhub:dev' 'sirepo_jupyterhub'
}
