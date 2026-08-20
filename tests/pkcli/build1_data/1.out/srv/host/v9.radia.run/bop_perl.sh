#!/bin/bash
bop_perl_rsconf_component() {
install_repo_eval biviosoftware/container-perl base
rsconf_install_perl_rpm 'bivio-perl' 'bivio-perl-dev.rpm' 'bivio-perl-20220722.195234-1.x86_64'
rsconf_install_perl_rpm 'perl-Bivio' 'perl-Bivio-dev.rpm' 'perl-Bivio-20220722.195252-1.x86_64'
}
