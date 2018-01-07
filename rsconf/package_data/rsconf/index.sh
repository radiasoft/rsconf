#!/bin/bash
set -eu -o pipefail
curl -s -S -L "$install_server/radiasoft/download/bin/install.sh" | bash -s rsconf.sh "$@"
