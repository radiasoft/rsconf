#!/bin/bash
#
# Build perl RPMs
#
. ~/.bashrc
set -euo pipefail

build_perl_main() {
    cd ~/src/radiasoft/rsconf
    export install_server=http://$(hostname -f):2916 install_channel=dev
    if curl --connect-timeout 1 "$install_server" >& /dev/null; then
        echo 'You need to:
    bash run/nginx/start.sh
in another window' 1>&2
        return 1
    fi
    cd ~/src/biviosoftware
    gcl rpm-perl
    gcl container-perl
    cd container-perl
    radia_run container-build
    cd ~/src/radiasoft/rsconf
    export rpm_perl_install_dir=$PWD/rpm
    radia_run biviosoftware/rpm-perl bivio-perl
    radia_run biviosoftware/rpm-perl Bivio
    radia_run biviosoftware/rpm-perl BivioOrg
}

build_perl_main "$@"
