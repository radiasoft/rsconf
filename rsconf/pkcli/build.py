"""Build the tree

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern import pkconfig
from pykern import pkio
from pykern.pkdebug import pkdp, pkdc, pkdlog, pkdexc
import grp
import os
import subprocess


class T(PKDict):
    def __init__(self, dbt, channel, host):
        super(T, self).__init__(
            components=PKDict(),
            components_required=[],
            dbt=dbt,
            hdb=dbt.host_db(channel, host),
        )

    def append_write_queue(self, compt):
        assert compt not in self._write_queue, "duplicate insert: {}".format(compt.name)
        self._write_queue.append(compt)

    def build_component(self, compt_or_name):
        from rsconf import component

        if isinstance(compt_or_name, component.T):
            compt = compt_or_name
            assert not self.components.get(
                compt.name
            ), "{}: duplicate component".format(compt.name)
        else:
            compt = self.components.get(compt_or_name)
            if compt:
                compt.assert_done()
                return
            compt = component.create_t(compt_or_name, self)
        self.components[compt.name] = compt
        compt.build_compile()
        # Must be after, since write_root_bash happens from this list and
        # dependencies in build_compile() must come first.
        self.components_required.append(compt.name)

    def create_host(self, dst_d):
        h = self.hdb.rsconf_db.host
        try:
            dst_d = dst_d.join(h)
            pkio.mkdir_parent(dst_d)
            self.hdb.build = PKDict(dst_d=dst_d)
            self._write_queue = []
            self._done_components = PKDict()
            d = self.hdb.rsconf_db
            self.require_component(*d.components)
            self._do_write_queue()
            self.write_root_bash(
                "000",
                [
                    f"rsconf_setup_vars '{d.channel}' '{d.os_release_id}' '{d.os_release_version_id }'"
                ]
                + ["rsconf_require " + x for x in self.components_required],
            )
        except Exception:
            pkdlog("{}: host failed:", h)
            raise

    def get_component(self, name, in_write_queue=True):
        if c := self._get_component(name):
            return c
        if in_write_queue:
            raise AssertionError(f"component not in write_queue: {name}")
        if c := self._done_components.get(name):
            return c
        raise AssertionError(f"component not found: {name}")

    def has_component(self, name):
        return bool(self._get_component(name))

    def require_component(self, *components):
        from rsconf import component

        for c in components:
            try:
                self.build_component(c)
            except Exception:
                pkdlog("{}: component failed:", c)
                raise

    def write_root_bash(self, basename, lines):
        # python and perl scripts?
        pkio.write_text(
            self.hdb.build.dst_d.join(basename + ".sh"),
            "\n".join(["#!/bin/bash"] + lines) + "\n",
        )

    def _do_write_queue(self):
        while self._write_queue:
            c = self._write_queue.pop(0)
            self._done_components[c.name] = c
            try:
                c.build_write()
            except Exception:
                pkdlog("{}: build_write failed:", c.name)
                raise

    def _get_component(self, name):
        for c in self._write_queue:
            if c.name == name:
                return c
        return None


def default_command():
    """Build the distribution tree"""
    from rsconf import db
    from pykern import pkunit

    def _instantiate():
        rv = []
        for c, hosts in dbt.channel_hosts().items():
            p = None
            for h in hosts:
                t = T(dbt, c, h)
                if "rsconf" in t.hdb.rsconf_db.components:
                    if p != None:
                        raise AssertionError(f"duplicate rsconf_host={h} first={p}")
                    p = t
                else:
                    rv.append(t)
        if not p:
            raise AssertionError(
                f"rsconf_host not found; one host must have 'rsconf' as component"
            )
        rv.insert(0, p)
        return rv

    if pkconfig.in_dev_mode():
        from rsconf.pkcli import setup_dev

        setup_dev.default_command()

    prev_umask = None
    try:
        prev_umask = os.umask(0o27)
        dbt = db.T()
        # Outside of srv_d so nginx doesn't see it. However,
        # make sure the same levels of directory so relative
        # links to rpm still work.
        # POSIT: srv_host_d is one level below srv_d
        tmp_d = (dbt.srv_d + "-tmp").join(dbt.srv_host_d.basename)
        old_d = tmp_d + "-old"
        new_d = tmp_d + "-new"
        pkio.unchecked_remove(new_d, old_d)
        pkio.mkdir_parent(new_d)
        for c, hosts in dbt.channel_hosts().items():
            for h in hosts:
                t = T(dbt, c, h)
                t.create_host(new_d)
        subprocess.check_call(["chgrp", "-R", db.cfg.srv_group, str(new_d)])
        subprocess.check_call(["chmod", "-R", "g+rX", str(new_d)])
        pkio.unchecked_remove(old_d)
        dst_d = dbt.srv_host_d
        if dst_d.check():
            dst_d.rename(old_d)
        new_d.rename(dst_d)
    finally:
        if prev_umask:
            os.umask(prev_umask)
