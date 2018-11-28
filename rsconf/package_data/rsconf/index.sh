#!/bin/bash
set -eu -o pipefail
if [[ ! ${install_server:-} ]]; then
    export install_server=https://rsconf.radiasoft.org
fi
curl -s -S -L "$install_server/radiasoft/download/bin/install.sh" | bash -s rsconf.sh "$@"
