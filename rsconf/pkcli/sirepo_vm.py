"""Set up sirepo VM for local dev testing

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern import pkio, pkjinja
from pykern.pkdebug import pkdc, pkdlog, pkdp
import os
import pwd
import subprocess


_ROOT_D = pkio.py_path("/srv/rsconf")
_RSCONF_SRC_D = pkio.py_path("~/src/radiasoft/rsconf")
_UPDATE_SH = _ROOT_D.join("update.sh")


def setup_dev():
    """Create /srv/rsconf with 000.yml and update.sh then build and install.

    Requires root privileges.
    """
    _write_000_yml(pwd.getpwuid(os.getuid()))
    _write_update_sh()
    subprocess.check_call(["bash", str(_UPDATE_SH)])


def _write_000_yml(user):
    pkjinja.render_resource(
        "sirepo-vm-dev/000.yml",
        PKDict(
            uid=user.pw_uid,
            user=user.pw_name,
        ),
        output=_ROOT_D.join("db", "000.yml"),
    )


def _write_update_sh():
    pkio.write_text(
        _UPDATE_SH,
        f"""#!/bin/bash
set -eou pipefail
pip install --quiet --editable {_RSCONF_SRC_D}
export RSCONF_DB_ROOT_D={_ROOT_D}
mkdir -p "$RSCONF_DB_ROOT_D"
rsconf build
bash {_ROOT_D}/srv/host/localhost/localhost.sh
""",
    )
    _UPDATE_SH.chmod(0o700)
