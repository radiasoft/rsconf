#!/bin/bash
umask 022
(
    umask 077
    mkdir /var/lib/rsconf/{db/secret,srv}
    chmod 711 /var/lib/rsconf
    chgrp nginx /var/lib/rsconf/srv
)
curl radia.run | bash -s redhat-base
yum install -y nginx
bivio_pyenv_2
cd ~/src
mkdir radiasoft
cd radiasoft
gcl pykern
cd pykern
pip install -e .
cd ..
gcl rsconf
cd rsconf
cat >> ~/.post_bivio_bashrc <<'EOF'
export PYKERN_PKCONFIG_CHANNEL=alpha
export RSCONF_DB_ROOT_D=/var/lib/rsconf
EOF

# extend /var
lvextend -L +125G /dev/vgdata/lvdata
xfs_growfs /mount/point -D size
