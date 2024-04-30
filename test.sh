#!/bin/bash
source ~/.bashrc
set -eou pipefail

_main() {
    # POSIT: directories needed by pkcli.setup_dev
    mkdir -p ~/src/{radiasoft,biviosoftware}
    cd ~/src/radiasoft
    gcl download
    cd -
    pykern ci run
}

_main "$@"
