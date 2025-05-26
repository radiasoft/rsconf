#!/bin/bash
set -eu -o pipefail
if [[ ! ${install_server:-} ]]; then
    export install_server=https://rsconf.radiasoft.org
fi
curl --fail --silent --show-error --location \
    "$install_server"/radiasoft/download/bin/install.sh \
    | bash ${install_debug:+-x} -s rsconf.sh "$@"
