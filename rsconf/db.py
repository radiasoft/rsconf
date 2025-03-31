"""Database

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern import pkconfig
from pykern import pkio
from pykern import pkjson
from pykern import pkresource
from pykern.pkdebug import pkdc, pkdlog, pkdp, pkdpretty
import collections
import copy
import random
import re
import string


VISIBILITY_LIST = ("global", "channel", "host")
VISIBILITY_DEFAULT = VISIBILITY_LIST[1]
VISIBILITY_GLOBAL = VISIBILITY_LIST[0]

ZERO_YML = "0*.yml"

USER_HOME_ROOT_D = pkio.py_path("/home")

LOCAL_IP = "127.0.0.1"
ANY_IP = "0.0.0.0"
DEFAULT_ROOT_SUBDIR = "run"
LEVELS = ("default", "channel", "host")
# Secrets are long so keep them simple
_BASE62_CHARS = string.ascii_lowercase + string.digits + string.ascii_uppercase
_HEX_CHARS = "0123456789abcdef"
_IGNORE_RE = re.compile(r"^(?:\.#|#)|~$")
_UNIT_TEST_ROOT_D = "UNIT TEST"


_GLOBAL_PATHS = None


class Host(PKDict):
    def __init__(self, raw, channel, host):
        c = global_paths_as_dict().pkupdate(
            channel=channel,
            host=host.lower(),
        )
        self._before_defaults(c)
        self._merge_levels(raw, c)
        self._after_defaults(c)
        self._assert_no_rsconf_db_values(self)
        self._update_paths(self)
        pkio.unchecked_remove(self.rsconf_db.tmp_d)
        pkio.mkdir_parent(self.rsconf_db.tmp_d)
        self.rsconf_db.is_centos7 = self.rsconf_db.host in raw.pkunchecked_nested_get(
            "rsconf_db.centos7_hosts", ()
        )
        if self.rsconf_db.is_centos7:
            self.rsconf_db.os_release_id = "centos"
            self.rsconf_db.os_release_version_id = "7"
        else:
            self.rsconf_db.os_release_id = "almalinux"
            self.rsconf_db.os_release_version_id = "9"
        pkjson.dump_pretty(self, filename=self.rsconf_db.tmp_d.join("db.json"))

    def j2_ctx_copy(self):
        return copy.deepcopy(self)

    def _after_defaults(self, common):
        self.pkmerge(
            PKDict(
                rsconf_db=PKDict(
                    # make sure has some value, base_os expects this
                    local_dirs=PKDict(),
                    local_files=_init_local_files(common),
                    resource_paths=_init_resource_paths(common),
                    # https://jnovy.fedorapeople.org/pxz/node1.html
                    # compression with 8 threads and max compression
                    # Useful (random) constants
                    compress_cmd="pxz -T8 -9",
                )
                .pkupdate(common)
                .pkupdate(
                    # overrides the global tmp_d
                    tmp_d=common.tmp_d.join(common.host),
                ),
            ),
        )
        # POSIT: required component defaults
        self.pksetdefault(
            component=PKDict,
        ).component.pksetdefault(
            tls_crt_create=pkconfig.in_dev_mode(),
            tls_crt=PKDict,
        )

    def _assert_no_rsconf_db_values(self, value, path=""):
        """If any value begins with RSCONF_DB_, should fail.

        Args:
            value (object): should not contain RSCONF_DB_.
        """
        if isinstance(value, dict):
            for k, v in value.items():
                self._assert_no_rsconf_db_values(k)
                self._assert_no_rsconf_db_values(v)
        elif isinstance(value, list):
            for v in value:
                self._assert_no_rsconf_db_values(v)
        elif isinstance(value, pkconfig.STRING_TYPES):
            if value.startswith("RSCONF_DB_"):
                raise AssertionError(
                    "value={} must not begin with RSCONF_DB_".format(value),
                )

    def _before_defaults(self, common):
        self.pkmerge(
            PKDict(
                rsconf_db=PKDict(
                    # Common defaults we allow overrides for
                    host_run_d="/srv",
                    run_u="vagrant",
                    root_u="root",
                    installer_url="https://radia.run",
                ).pkupdate(common)
            ),
        )

    def _merge_levels(self, raw, common):
        for l in LEVELS:
            v = raw[l]
            if l != LEVELS[0]:
                v = v.get(common.channel)
                if not v:
                    continue
                if l == LEVELS[2]:
                    v = v.get(common.host)
                    if not v:
                        continue
            self.pkmerge(copy.deepcopy(v))

    def __str(self, v):
        if isinstance(v, dict):
            res = PKDict()
            for k, v in v.items():
                res[str(k)] = self.__str(v)
            return res
        if isinstance(v, (list, tuple)):
            return [self.__str(x) for x in v]
        return str(v)

    def _update_paths(self, base):
        """If a path ends with ``_f`` or ``_d``, make it a py.path

        Args:
            base (dict): may contain paths
        """
        for k in list(base.keys()):
            if k.endswith(("_d", "_f")):
                base[k] = pkio.py_path(base[k])
            elif isinstance(base[k], dict):
                self._update_paths(base[k])


class T(PKDict):
    def __init__(self, *args, **kwargs):
        super(T, self).__init__(*args, **kwargs)
        b = global_paths_as_dict()
        self.pkupdate(copy.deepcopy(b))
        pkio.mkdir_parent(self.tmp_d)
        self.base = self._init_fconf(PKDict(rsconf_db=b))

    def channel_hosts(self):
        res = PKDict()
        for c in pkconfig.VALID_CHANNELS:
            res[c] = sorted(
                self.base.host.get(c, PKDict()).keys(),
            )
        return res

    def host_db(self, *args, **kwargs):
        return Host(self.base, *args, **kwargs)

    def _init_fconf(self, base_vars):
        from pykern import fconf
        import itertools, functools

        f = functools.reduce(
            lambda r, i: r + pkio.sorted_glob(i[0].join(i[1])),
            itertools.product(
                (self.db_d, self.secret_d),
                ("*.py", ZERO_YML),
            ),
            [],
        )
        if not f:
            raise ValueError(f"no files in db_d={self.db_d}")
        return fconf.Parser(files=f, base_vars=base_vars).result


def global_path(name):
    """Get global path by name

    Args:
        name (str): db_d, root_d, etc.
    Returns:
        py.path: path corresponding to `name`
    """

    def _dict():
        global _GLOBAL_PATHS
        if _GLOBAL_PATHS is not None:
            return _GLOBAL_PATHS
        # Slower but necessary, because tests can change root
        if cfg.root_d == _UNIT_TEST_ROOT_D:
            return global_paths_as_dict()
        _GLOBAL_PATHS = global_paths_as_dict()
        return _GLOBAL_PATHS

    return _dict()[name]


def global_paths_as_dict():
    """All global paths

    Returns:
        PKDict: new copy of all paths
    """
    rv = PKDict(
        root_d=pkio.py_path() if cfg.root_d == _UNIT_TEST_ROOT_D else cfg.root_d,
    )
    rv.pkupdate(
        db_d=rv.root_d.join("db"),
        etc_d=rv.root_d.join("etc"),
        proprietary_source_d=rv.root_d.join("proprietary"),
        rpm_source_d=rv.root_d.join("rpm"),
        srv_d=rv.root_d.join("srv"),
        tmp_d=rv.root_d.join("tmp"),
    ).pkupdate(
        local_d=rv.db_d.join("local"),
        resource_base_d=rv.db_d.join("resource"),
        secret_d=rv.db_d.join("secret"),
        srv_host_d=rv.srv_d.join("host"),
    ).pkupdate(
        tls_d=rv.secret_d.join("tls"),
    )
    return rv


def merge_dict(base, new):
    for k in list(new.keys()):
        new_v = new[k]
        if not k in base:
            base[k] = copy.deepcopy(new_v)
            continue
        base_v = base[k]
        if isinstance(new_v, dict) and "RSCONF_DB_REPLACE" in new_v:
            # replacement is the value of key "RSCONF_DB_REPLACE"
            x = new_v.pkdel("RSCONF_DB_REPLACE")
            if isinstance(x, dict):
                # give precendence to rsconf_db for replacements
                merge_dict(new_v, x)
            else:
                new_v = x
        elif isinstance(new_v, dict) or isinstance(base_v, dict):
            if new_v is None or base_v is None:
                # Just replace, because new_v overrides type in case of None
                pass
            elif isinstance(new_v, dict) and isinstance(base_v, dict):
                merge_dict(base_v, new_v)
                continue
            else:
                raise AssertionError(
                    "{}: type mismatch between new value ({}) and base ({})".format(
                        k, new_v, base_v
                    )
                )
        elif isinstance(new_v, list) or isinstance(base_v, list):
            if new_v is None or base_v is None:
                # Just replace, because new_v overrides type in case of None
                pass
            elif isinstance(new_v, list) and isinstance(base_v, list):
                # prepend the new values
                base[k] = copy.deepcopy(new_v) + base_v
                # strings, numbers, etc. are hashable, but dicts and lists are not.
                # this test ensures we don't have dup entries in lists.
                y = [x for x in base[k] if isinstance(x, collections.abc.Hashable)]
                assert len(set(y)) == len(
                    y
                ), "duplicates in key={} list values={}".format(k, base[k])
                continue
            else:
                raise AssertionError(
                    "{}: type mismatch between new value ({}) and base ({})".format(
                        k, new_v, base_v
                    )
                )
        elif type(new_v) != type(base_v) and not (
            isinstance(new_v, pkconfig.STRING_TYPES)
            and isinstance(base_v, pkconfig.STRING_TYPES)
            or new_v is None
            or base_v is None
        ):
            raise AssertionError(
                "{}: type mismatch between new value ({}) and base ({})".format(
                    k, new_v, base_v
                )
            )
        base[k] = copy.deepcopy(new_v)


def random_string(length=32, is_hex=False):
    chars = _HEX_CHARS if is_hex else _BASE62_CHARS
    r = random.SystemRandom()
    return "".join(r.choice(chars) for _ in range(length))


def resource_path(hdb, filename):
    for p in hdb.rsconf_db.resource_paths:
        res = p.join(filename)
        if res.check():
            return res
    return pkresource.file_path(filename)


def secret_path(hdb, filename, visibility=None, qualifier=None, directory=False):
    if visibility:
        assert (
            visibility in VISIBILITY_LIST
        ), "{}: invalid visibility, must be {}".format(
            visibility,
            VISIBILITY_LIST,
        )
    else:
        visibility = VISIBILITY_DEFAULT
    p = (
        []
        if visibility == VISIBILITY_GLOBAL
        else [qualifier or hdb.rsconf_db[visibility]]
    )
    p.append(filename)
    res = hdb.rsconf_db.secret_d.join(*p)
    pkio.mkdir_parent(res) if directory else pkio.mkdir_parent_only(res)
    return res


def user_home_path(user):
    return USER_HOME_ROOT_D.join(user)


@pkconfig.parse_none
def _cfg_root(value):
    """Parse root directory"""
    # TODO(robnagler) encapsulate this sirepo.server is the same thing
    from pykern import pkio, pkinspect, pkunit
    import os, sys

    if value:
        assert os.path.isabs(value), "{}: must be absolute".format(value)
        value = pkio.py_path(value)
        assert value.check(dir=1), "{}: must be a directory and exist".format(value)
    else:
        assert pkconfig.in_dev_mode(), "must be configured except in DEV"
        if pkunit.is_test_run():
            return _UNIT_TEST_ROOT_D
        fn = pkio.py_path(sys.modules[pkinspect.root_package(_cfg_root)].__file__)
        root = pkio.py_path(pkio.py_path(fn.dirname).dirname)
        # Check to see if we are in our ~/src/radiasoft/<pkg> dir. This is a hack,
        # but should be reliable.
        if not root.join("pyproject.toml").check():
            # Don't run from an install directory
            root = pkio.py_path(".")
        value = root.join(DEFAULT_ROOT_SUBDIR)
    return value


@pkconfig.parse_none
def _cfg_srv_group(value):
    """Set srv_group"""
    import grp
    import os

    if value:
        return grp.getgrnam(value).gr_name
    assert pkconfig.in_dev_mode(), "must be configured except in DEV"
    return grp.getgrgid(os.getgid()).gr_name


def _init_local_files(rsconf_db):
    r = rsconf_db.local_d
    res = PKDict()
    for l in LEVELS[0], rsconf_db.channel, rsconf_db.host:
        d = r.join(l)
        for s in pkio.walk_tree(d):
            if _IGNORE_RE.search(s.basename):
                continue
            res["/" + d.bestrelpath(s)] = PKDict(_source=s)
    return res


def _init_resource_paths(rsconf_db):
    res = [rsconf_db.resource_base_d]
    for i in rsconf_db.channel, rsconf_db.host:
        res.insert(0, res[0].join(i))
    return res


cfg = pkconfig.init(
    root_d=(None, _cfg_root, "Top of rsconf tree"),
    srv_group=(None, _cfg_srv_group, "Group id of files to srv directory"),
)
