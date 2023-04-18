#!/bin/bash
sirepo_job_supervisor_rsconf_component() {
rsconf_service_prepare 'sirepo_job_supervisor' '/etc/systemd/system/sirepo_job_supervisor.service' '/etc/systemd/system/sirepo_job_supervisor.service.d' '/srv/sirepo_job_supervisor'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_job_supervisor/cmd' '56f5b740b841469890bc336dd52007f9'
rsconf_install_file '/srv/sirepo_job_supervisor/env' '482f2983aa80ba9bcea9c00f7f6b8b18'
rsconf_install_file '/srv/sirepo_job_supervisor/remove' 'f69212ff96cee7286608d13de38cfb1a'
rsconf_install_file '/srv/sirepo_job_supervisor/start' 'c62a7cbf3d5ba3125f9517a0091c3be1'
rsconf_install_file '/srv/sirepo_job_supervisor/stop' 'e9c30ba96db25b8babf1c9c281087fbb'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo_job_supervisor.service' '1953774ea62c5c1a091580374385870b'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/sirepo:dev' 'sirepo_job_supervisor'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor/docker_tls'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor/docker_tls/v4.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v4.radia.run/cacert.pem' '821c1182ee9529bfdae5bbd509fe9299'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v4.radia.run/cert.pem' 'fdca96202eec3aff2f0e55a7de43282c'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v4.radia.run/key.pem' '75d41e9f2399fdd068c94579095bcb7a'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/docker-job-supervisor-sirepo.v4.radia.run.conf' 'da4dabae422925bb1b9b11c53540e3d9'
}
