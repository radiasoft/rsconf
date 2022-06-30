#!/bin/bash
sirepo_job_supervisor_rsconf_component() {
rsconf_service_prepare 'sirepo_job_supervisor' '/etc/systemd/system/sirepo_job_supervisor.service' '/etc/systemd/system/sirepo_job_supervisor.service.d' '/srv/sirepo_job_supervisor'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_job_supervisor/cmd' '56f5b740b841469890bc336dd52007f9'
rsconf_install_file '/srv/sirepo_job_supervisor/env' '456fdd262db12f4598c46967b1661b6c'
rsconf_install_file '/srv/sirepo_job_supervisor/remove' '7ed3f2d2d496a9545920e00a585cb014'
rsconf_install_file '/srv/sirepo_job_supervisor/start' '09cb9ea5098dc63f20abd10137c8be66'
rsconf_install_file '/srv/sirepo_job_supervisor/stop' 'aa7c6cd6cf57f361d6b38f474a89562d'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo_job_supervisor.service' 'b222a34b2fe807b5d305687763fd66a7'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/sirepo:dev' 'sirepo_job_supervisor'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor/docker_tls'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_job_supervisor/docker_tls/v9.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v9.radia.run/cacert.pem' '4b670b08c82a17b5bfbdfc470b444ad5'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v9.radia.run/cert.pem' '9bf8e30f1906deb2dc8ef9b8e3677ec3'
rsconf_install_file '/srv/sirepo_job_supervisor/docker_tls/v9.radia.run/key.pem' '737ecfd7c000fe3a49fc34346ea37819'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/docker-job-supervisor-sirepo.v4.radia.run.conf' 'e84a5488b7520c06a5fd6eea5766810d'
}
