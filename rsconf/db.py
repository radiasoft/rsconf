# -*- coding: utf-8 -*-
"""Database

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
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

SRV_SUBDIR = "srv"
DEFAULT_ROOT_SUBDIR = "run"
DB_SUBDIR = "db"
LOCAL_SUBDIR = "local"
PROPRIETARY_SUBDIR = "proprietary"
RPM_SUBDIR = "rpm"
SECRET_SUBDIR = "secret"
RESOURCE_SUBDIR = "resource"
TMP_SUBDIR = "tmp"
HOST_SUBDIR = "host"
LEVELS = ("default", "channel", "host")
# Secrets are long so keep them simple
_BASE62_CHARS = string.ascii_lowercase + string.digits + string.ascii_uppercase
_HEX_CHARS = "0123456789abcdef"
_IGNORE_RE = re.compile(r"^(?:\.#|#)|~$")
_UNIT_TEST_ROOT_D = "UNIT TEST"


class Host(PKDict):
    def j2_ctx_copy(self):
        return copy.deepcopy(self)

    def __str(self, v):
        if isinstance(v, dict):
            res = PKDict()
            for k, v in v.items():
                res[str(k)] = self.__str(v)
            return res
        if isinstance(v, (list, tuple)):
            return [self.__str(x) for x in v]
        return str(v)


class T(PKDict):
    def __init__(self, *args, **kwargs):
        super(T, self).__init__(*args, **kwargs)
        self.root_d = root_d()
        self.db_d = self.root_d.join(DB_SUBDIR)
        self.proprietary_source_d = self.root_d.join(PROPRIETARY_SUBDIR)
        self.rpm_source_d = self.root_d.join(RPM_SUBDIR)
        self.tmp_d = self.root_d.join(TMP_SUBDIR)
        self.secret_d = self.db_d.join(SECRET_SUBDIR)
        self.srv_d = self.root_d.join(SRV_SUBDIR)
        self.srv_host_d = self.srv_d.join(HOST_SUBDIR)
        pkio.mkdir_parent(self.tmp_d)
        self.base = self._init_fconf() if cfg.fconf else self._init_jinja()

    def channel_hosts(self):
        res = PKDict()
        for c in pkconfig.VALID_CHANNELS:
            res[c] = sorted(
                self.base.host.get(c, PKDict()).keys(),
            )
        return res

    def host_db(self, *args):
        return self._host_db_fconf(*args) if cfg.fconf else self._host_db_jinja(*args)

    def _host_db_fconf(self, channel, host):
        c = PKDict(
            channel=channel,
            db_d=self.db_d,
            host=host.lower(),
        )
        res = Host().pkmerge(
            PKDict(
                rsconf_db=PKDict(
                    # Common defaults we allow overrides for
                    host_run_d="/srv",
                    run_u="vagrant",
                    root_u="root",
                ).pkupdate(c)
            ),
        )
        for l in LEVELS:
            v = self.base[l]
            if l != LEVELS[0]:
                v = v.get(channel)
                if not v:
                    continue
                if l == LEVELS[2]:
                    v = v.get(host)
                    if not v:
                        continue
            res.pkmerge(copy.deepcopy(v))
        res.pkmerge(
            PKDict(
                rsconf_db=PKDict(
                    db_d=self.db_d,
                    host=host,
                    local_files=_init_local_files(c),
                    proprietary_source_d=self.proprietary_source_d,
                    resource_paths=_init_resource_paths(c),
                    rpm_source_d=self.rpm_source_d,
                    secret_d=self.secret_d,
                    srv_d=self.srv_d,
                    srv_host_d=self.srv_host_d,
                    tmp_d=self.tmp_d.join(host),
                    # https://jnovy.fedorapeople.org/pxz/node1.html
                    # compression with 8 threads and max compression
                    # Useful (random) constants
                    compress_cmd="pxz -T8 -9",
                ).pkupdate(c),
            ),
        )
        _assert_no_rsconf_db_values(res)
        _update_paths(res)
        pkio.unchecked_remove(res.rsconf_db.tmp_d)
        pkio.mkdir_parent(res.rsconf_db.tmp_d)
        pkjson.dump_pretty(res, filename=res.rsconf_db.tmp_d.join("db.json"))
        return res

    def _host_db_jinja(self, channel, host):
        c = PKDict(
            channel=channel,
            db_d=self.db_d,
            host=host.lower(),
        )
        res = Host()
        v = PKDict(
            rsconf_db=PKDict(
                # Common defaults we allow overrides for
                host_run_d="/srv",
                run_u="vagrant",
                root_u="root",
            ).pkupdate(c)
        )
        merge_dict(res, v)
        for l in LEVELS:
            v = self.base[l]
            if l != LEVELS[0]:
                v = v.get(channel)
                if not v:
                    continue
                if l == LEVELS[2]:
                    v = v.get(host)
                    if not v:
                        continue
            merge_dict(res, v)
        v = PKDict(
            rsconf_db=PKDict(
                db_d=self.db_d,
                host=host,
                local_files=_init_local_files(c),
                proprietary_source_d=self.proprietary_source_d,
                resource_paths=_init_resource_paths(c),
                rpm_source_d=self.rpm_source_d,
                secret_d=self.secret_d,
                srv_d=self.srv_d,
                srv_host_d=self.srv_host_d,
                tmp_d=self.tmp_d.join(host),
                # https://jnovy.fedorapeople.org/pxz/node1.html
                # compression with 8 threads and max compression
                # Useful (random) constants
                compress_cmd="pxz -T8 -9",
            ).pkupdate(c),
        )
        pkio.unchecked_remove(v.rsconf_db.tmp_d)
        pkio.mkdir_parent(v.rsconf_db.tmp_d)
        merge_dict(res, v)
        _assert_no_rsconf_db_values(res)
        _update_paths(res)
        pkjson.dump_pretty(res, filename=res.rsconf_db.tmp_d.join("db.json"))
        return res

    def _init_fconf(self):
        from pykern import fconf
        import itertools, functools

        return fconf.Parser(
            functools.reduce(
                lambda r, i: r + pkio.sorted_glob(i[0].join(i[1])),
                itertools.product(
                    (self.db_d, self.secret_d),
                    ("*.py", ZERO_YML),
                ),
                [],
            ),
        ).result

    def _init_jinja(self):
        from pykern import pkjinja
        from pykern import pkyaml

        res = PKDict()
        f = None
        try:
            for d in self.db_d, self.secret_d:
                for f in pkio.sorted_glob(d.join(ZERO_YML)):
                    v = pkjinja.render_file(f, res, strict_undefined=True)
                    pkio.write_text(self.tmp_d.join(f.basename), str(v))
                    v = pkyaml.load_str(v)
                    merge_dict(res, v)
        except Exception:
            pkdlog("error rendering db={}", f)
            raise
        return res


def root_d():
    """Root directory for db and host

    Returns:
        py.path: directory
    """
    if cfg.root_d == _UNIT_TEST_ROOT_D:
        return pkio.py_path()
    return cfg.root_d


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
    return pkresource.filename(filename)


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


def user_home_path(hdb, user):
    return USER_HOME_ROOT_D.join(user)


def _assert_no_rsconf_db_values(value, path=""):
    """If any value begins with RSCONF_DB_, should fail.

    Args:
        value (object): should not contain RSCONF_DB_.
    """
    if isinstance(value, dict):
        for k, v in value.items():
            _assert_no_rsconf_db_values(k)
            _assert_no_rsconf_db_values(v)
    elif isinstance(value, list):
        for v in value:
            _assert_no_rsconf_db_values(v)
    elif isinstance(value, pkconfig.STRING_TYPES):
        if value.startswith("RSCONF_DB_"):
            raise AssertionError(
                "value={} must not begin with RSCONF_DB_".format(value),
            )


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
        assert pkconfig.channel_in("dev"), "must be configured except in DEV"
        if pkunit.is_test_run():
            return _UNIT_TEST_ROOT_D
        fn = pkio.py_path(sys.modules[pkinspect.root_package(_cfg_root)].__file__)
        root = pkio.py_path(pkio.py_path(fn.dirname).dirname)
        # Check to see if we are in our ~/src/radiasoft/<pkg> dir. This is a hack,
        # but should be reliable.
        if not root.join("setup.py").check():
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
    assert pkconfig.channel_in("dev"), "must be configured except in DEV"
    return grp.getgrgid(os.getgid()).gr_name


def _init_local_files(rsconf_db):
    r = rsconf_db.db_d.join(LOCAL_SUBDIR)
    res = PKDict()
    for l in LEVELS[0], rsconf_db.channel, rsconf_db.host:
        d = r.join(l)
        for s in pkio.walk_tree(d):
            if _IGNORE_RE.search(s.basename):
                continue
            res["/" + d.bestrelpath(s)] = PKDict(_source=s)
    return res


def _init_resource_paths(rsconf_db):
    res = [rsconf_db.db_d.join(RESOURCE_SUBDIR)]
    for i in rsconf_db.channel, rsconf_db.host:
        res.insert(0, res[0].join(i))
    return res


def _update_paths(base):
    """If a path ends with ``_f`` or ``_d``, make it a py.path

    Args:
        base (dict): may contain paths
    """
    for k in list(base.keys()):
        if k.endswith(("_d", "_f")):
            base[k] = pkio.py_path(base[k])
        elif isinstance(base[k], dict):
            _update_paths(base[k])


cfg = pkconfig.init(
    fconf=(True, bool, "Use pykern.fconf for reading db"),
    root_d=(None, _cfg_root, "Top of rsconf tree"),
    srv_group=(None, _cfg_srv_group, "Group id of files to srv directory"),
)
