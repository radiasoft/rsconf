# -*- coding: utf-8 -*-
u"""Database

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern import pkconfig
from pykern import pkio
from pykern import pkjinja
from pykern import pkjson
from pykern import pkresource
from pykern import pkyaml
from pykern.pkdebug import pkdc, pkdlog, pkdp, pkdpretty
import collections
import copy
import random
import string


VISIBILITY_LIST = ('global', 'channel', 'host')
VISIBILITY_DEFAULT = VISIBILITY_LIST[1]
VISIBILITY_GLOBAL = VISIBILITY_LIST[0]

ZERO_YML = '0*.yml'

USER_HOME_ROOT_D = pkio.py_path('/home')

SRV_SUBDIR = 'srv'
DEFAULT_ROOT_SUBDIR = 'run'
DB_SUBDIR = 'db'
LOCAL_SUBDIR = 'local'
PROPRIETARY_SUBDIR = 'proprietary'
RPM_SUBDIR = 'rpm'
SECRET_SUBDIR = 'secret'
RESOURCE_SUBDIR = 'resource'
TMP_SUBDIR = 'tmp'
HOST_SUBDIR = 'host'
LEVELS = ('default', 'channel', 'host')
# Secrets are long so keep them simple
_BASE62_CHARS = string.ascii_lowercase + string.digits + string.ascii_uppercase
_HEX_CHARS = '0123456789abcdef'


class Host(PKDict):
    def j2_ctx_copy(self):
        return copy.deepcopy(self)

    def __repr__(self):
        """Writes tmp_d/db.json and returns filename

        This is a hack to support pkdc below.
        """
        f = self.rsconf_db.tmp_d.join('db.json')
        if self.rsconf_db.tmp_d:
            pkjson.dump_pretty(self.__str(self), filename=f)
        return str(f)

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
        self.root_d = pkio.py_path(cfg.root_d)
        self.db_d = self.root_d.join(DB_SUBDIR)
        self.proprietary_source_d = self.root_d.join(PROPRIETARY_SUBDIR)
        self.rpm_source_d = self.root_d.join(RPM_SUBDIR)
        self.tmp_d = self.root_d.join(TMP_SUBDIR)
        self.secret_d = self.db_d.join(SECRET_SUBDIR)
        self.srv_d = self.root_d.join(SRV_SUBDIR)
        self.srv_host_d = self.srv_d.join(HOST_SUBDIR)
        self.base = PKDict()
        f = None
        try:
            for d in self.db_d, self.secret_d:
                for f in pkio.sorted_glob(d.join(ZERO_YML)):
                    v = pkyaml.load_str(
                        pkjinja.render_file(
                            f,
                            self.base,
                            strict_undefined=True,
                        ),
                    )
                    merge_dict(self.base, v)
        except Exception:
            pkdlog('error rendering db={}', f)
            raise

    def channel_hosts(self):
        res = PKDict()
        for c in pkconfig.VALID_CHANNELS:
            res[c] = sorted(
                self.base.host.get(c, PKDict()).keys(),
            )
        return res

    def host_db(self, channel, host):
        res = Host()
        v = PKDict(
            rsconf_db=PKDict(
                # Common defaults we allow overrides for
                host_run_d='/srv',
                run_u='vagrant',
                root_u='root',
            )
        )
        merge_dict(res, v)
        #TODO(robnagler) optimize by caching default and channels
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
        host = host.lower()
        v = PKDict(
            rsconf_db=PKDict(
                channel=channel,
                db_d=self.db_d,
                host=host,
                proprietary_source_d=self.proprietary_source_d,
                rpm_source_d=self.rpm_source_d,
                secret_d=self.secret_d,
                srv_d=self.srv_d,
                srv_host_d=self.srv_host_d,
                tmp_d=self.tmp_d.join(host),
                # https://jnovy.fedorapeople.org/pxz/node1.html
                # compression with 8 threads and max compression
                # Useful (random) constants
                compress_cmd='pxz -T8 -9',
            )
        )
        v.rsconf_db.resource_paths = _init_resource_paths(v)
        v.rsconf_db.local_files = _init_local_files(v)
        pkio.unchecked_remove(v.rsconf_db.tmp_d)
        pkio.mkdir_parent(v.rsconf_db.tmp_d)
        merge_dict(res, v)
        _assert_no_rsconf_db_values(res)
        _update_paths(res)
        pkdc('{}', res)
        return res


def merge_dict(base, new):
    for k in list(new.keys()):
        new_v = new[k]
        if not k in base:
            base[k] = copy.deepcopy(new_v)
            continue
        base_v = base[k]
        if isinstance(new_v, dict) and len(new_v) == 1 and \
           'RSCONF_DB_REPLACE' in new_v:
            # replacement is the value of key "RSCONF_DB_REPLACE"
            new_v = new_v.RSCONF_DB_REPLACE
        elif isinstance(new_v, dict) or isinstance(base_v, dict):
            if new_v is None or base_v is None:
                # Just replace, because new_v overrides type in case of None
                pass
            elif isinstance(new_v, dict) and isinstance(base_v, dict):
                merge_dict(base_v, new_v)
                continue
            else:
                raise AssertionError(
                    '{}: type mismatch between new value ({}) and base ({})'.format(
                        k, new_v, base_v))
        elif isinstance(new_v, list) or isinstance(base_v, list):
            if new_v is None or base_v is None:
                # Just replace, because new_v overrides type in case of None
                pass
            elif isinstance(new_v, list) and isinstance(base_v, list):
                # prepend the new values
                base[k] = copy.deepcopy(new_v) + base_v
                # strings, numbers, etc. are hashable, but dicts and lists are not.
                # this test ensures we don't have dup entries in lists.
                y = [x for x in base[k] if isinstance(x, collections.Hashable)]
                assert len(set(y)) == len(y), \
                    'duplicates in key={} list values={}'.format(k, base[k])
                continue
            else:
                raise AssertionError(
                    '{}: type mismatch between new value ({}) and base ({})'.format(
                        k, new_v, base_v))
        elif type(new_v) != type(base_v) and not (
            isinstance(new_v, pkconfig.STRING_TYPES) and isinstance(base_v, pkconfig.STRING_TYPES)
            or new_v is None or base_v is None
        ):
            raise AssertionError(
                '{}: type mismatch between new value ({}) and base ({})'.format(
                    k, new_v, base_v))
        base[k] = copy.deepcopy(new_v)


def random_string(length=32, is_hex=False):
    chars = _HEX_CHARS if is_hex else _BASE62_CHARS
    r = random.SystemRandom()
    return ''.join(r.choice(chars) for _ in range(length))


def resource_path(hdb, filename):
    for p in hdb.rsconf_db.resource_paths:
        res = p.join(filename)
        if res.check():
            return res
    return pkresource.filename(filename)


def secret_path(hdb, filename, visibility=None, qualifier=None):
    if visibility:
        assert visibility in VISIBILITY_LIST, \
            '{}: invalid visibility, must be {}'.format(
                visibility,
                VISIBILITY_LIST,
            )
    else:
        visibility = VISIBILITY_DEFAULT
    p = [] if visibility == VISIBILITY_GLOBAL else [qualifier or hdb.rsconf_db[visibility]]
    p.append(filename)
    res = hdb.rsconf_db.secret_d.join(*p)
    pkio.mkdir_parent_only(res)
    return res


def user_home_path(hdb, user):
    return USER_HOME_ROOT_D.join(user)


def _assert_no_rsconf_db_values(value, path=''):
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
        if value.startswith('RSCONF_DB_'):
            raise AssertionError(
                'value={} must not begin with RSCONF_DB_'.format(value),
            )


@pkconfig.parse_none
def _cfg_root(value):
    """Parse root directory"""
    #TODO(robnagler) encapsulate this sirepo.server is the same thing
    from pykern import pkio, pkinspect
    import os, sys

    if value:
        assert os.path.isabs(value), \
            '{}: must be absolute'.format(value)
        value = pkio.py_path(value)
        assert value.check(dir=1), \
            '{}: must be a directory and exist'.format(value)
    else:
        assert pkconfig.channel_in('dev'), \
            'must be configured except in DEV'
        fn = pkio.py_path(sys.modules[pkinspect.root_package(_cfg_root)].__file__)
        root = pkio.py_path(pkio.py_path(fn.dirname).dirname)
        # Check to see if we are in our ~/src/radiasoft/<pkg> dir. This is a hack,
        # but should be reliable.
        if not root.join('setup.py').check():
            # Don't run from an install directorya
            root = pkio.py_path('.')
        value = root.join(DEFAULT_ROOT_SUBDIR)
    return value

@pkconfig.parse_none
def _cfg_srv_group(value):
    """Set srv_group"""
    import grp
    import os

    if value:
        return grp.getgrnam(value).gr_name
    assert pkconfig.channel_in('dev'), \
        'must be configured except in DEV'
    return grp.getgrgid(os.getgid()).gr_name


def _init_local_files(values):
    v = values.rsconf_db
    r = v.db_d.join(LOCAL_SUBDIR)
    res = PKDict()
    for l in LEVELS[0], v.channel, v.host:
        d = r.join(l)
        for f in pkio.walk_tree(d):
            res['/' + d.bestrelpath(f)] = f
    return res


def _init_resource_paths(values):
    v = values.rsconf_db
    res = [v.db_d.join(RESOURCE_SUBDIR)]
    for i in values.rsconf_db.channel, values.rsconf_db.host:
        res.insert(0, res[0].join(i))
    return res


def _update_paths(base):
    """If a path ends with ``_f`` or ``_d``, make it a py.path

    Args:
        base (dict): may contain paths
    """
    for k in list(base.keys()):
        if k.endswith(('_d', '_f')):
            base[k] = pkio.py_path(base[k])
        elif isinstance(base[k], dict):
            _update_paths(base[k])


cfg = pkconfig.init(
    root_d=(None, _cfg_root, 'Top of rsconf tree'),
    srv_group=(None, _cfg_srv_group, 'Group id of files to srv directory'),
)
