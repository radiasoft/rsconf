#!/bin/bash
sirepo_job_supervisor_rsconf_component() {
rsconf_service_prepare 'sirepo_job_supervisor' '/etc/systemd/system/sirepo_job_supervisor.service' '/etc/systemd/system/sirepo_job_supervisor.service.d' '/srv/sirepo_job_supervisor'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_job_supervisor/cmd' '56f5b740b841469890bc336dd52007f9'
rsconf_install_file '/srv/sirepo_job_supervisor/env' '4f090b9dbca4c1345d6ca0d7241bad1e'
rsconf_install_file '/srv/sirepo_job_supervisor/remove' 'f69212ff96cee7286608d13de38cfb1a'
rsconf_install_file '/srv/sirepo_job_supervisor/start' '653e41b6ea9f8ff5f8b2f5f092f400c1'
rsconf_install_file '/srv/sirepo_job_supervisor/stop' 'e9c30ba96db25b8babf1c9c281087fbb'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo_job_supervisor.service' '1953774ea62c5c1a091580374385870b'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/sirepo:dev' 'sirepo_job_supervisor' 'sirepo_job_supervisor' ''
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor/docker_tls'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor/docker_tls/v9.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v9.radia.run/cacert.pem' '4b670b08c82a17b5bfbdfc470b444ad5'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v9.radia.run/cert.pem' '9bf8e30f1906deb2dc8ef9b8e3677ec3'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v9.radia.run/key.pem' '737ecfd7c000fe3a49fc34346ea37819'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/docker-job-supervisor-sirepo.v4.radia.run.conf' '44f649da13034f7533dd08720db0c535'
}
