# -*- coding: utf-8 -*-
"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp, pkdlog
from pykern import pkjson
from rsconf import component
import copy


_CONF_F = "conf.py"
_USER_SUBDIR = "user"
_DOCKER_TLS_SUBDIR = "docker_tls"
_DEFAULT_PORT_BASE = 8100
# POSIT: rsdockerspawner._DEFAULT_POOL_NAME
_EVERYBODY = "everybody"
DEFAULT_USER_GROUP = _EVERYBODY
_DEFAULT_POOL = _EVERYBODY
_DEFAULT_MOCK_PASSWORD = "testpass"


class T(component.T):
    _COOKIE_SECRET = "jupyterhub_cookie_secret"
    _PROXY_AUTH = "jupyterhub_proxy_auth"

    def internal_build_compile(self):
        from rsconf import db
        from rsconf import systemd
        from rsconf.component import docker_registry

        self.buildt.require_component("docker")
        jc, z = self.j2_ctx_init()
        self.__run_d = systemd.unit_run_d(jc, self.name)
        self.__conf_f = self.__run_d.join(_CONF_F)
        systemd.docker_unit_prepare(
            self,
            jc,
            docker_exec=f"bash -l -c 'jupyterhub -f {self.__conf_f}'",
        )
        z.setdefault("jupyter_docker_image_is_local", False)
        z.update(
            user_d=self._jupyterhub_db().join(_USER_SUBDIR),
            jupyter_docker_image=docker_registry.absolute_image(
                self,
                image=z.jupyter_docker_image,
                image_is_local=z.jupyter_docker_image_is_local,
            ),
            run_u=jc.rsconf_db.run_u,
            jupyter_run_u=jc.rsconf_db.run_u,
        )
        z.setdefault("http_timeout", 30)
        z.setdefault("template_vars", {})
        self._network(z, jc)
        z.admin_users_str = _list_to_str(z.admin_users)
        z.home_d = db.user_home_path(z.jupyter_run_u)
        z.cookie_secret_hex = self.secret_path_value(
            self._COOKIE_SECRET,
            gen_secret=lambda: db.random_string(length=64, is_hex=True),
            visibility="channel",
        )[0]
        z.proxy_auth_token = self.secret_path_value(
            self._PROXY_AUTH,
            gen_secret=lambda: db.random_string(length=64, is_hex=True),
            visibility="channel",
        )[0]
        self._rsdockerspawner(z)

    def internal_build_write(self):
        from rsconf import db
        from rsconf.component import docker
        from rsconf.component import docker_registry

        z = self.j2_ctx[self.name]
        self._auth(z)
        self._install_jupyterhub_db(z)
        self.install_access(mode="711", owner=z.run_u)
        self.install_directory(self.__run_d)
        self.install_access(mode="700", owner=z.jupyter_run_u)
        self.install_directory(z.user_d)
        self.install_access(mode="400", owner=z.run_u)
        self.install_resource(f"{self.name}/{_CONF_F}", self.j2_ctx, self.__conf_f)
        docker.setup_cluster(
            self,
            hosts=z.docker_hosts,
            tls_d=z.tls_d,
            run_u=z.run_u,
            j2_ctx=self.j2_ctx,
        )
        if not docker_registry.image_is_local(
            self,
            image=z.jupyter_docker_image,
            image_is_local=z.jupyter_docker_image_is_local,
        ):
            self.append_root_bash(
                "rsconf_service_docker_pull '{}'".format(z.jupyter_docker_image),
            )
        self._enable_docker()

    def _auth(self, z):
        if self.j2_ctx.rsconf_db.channel == "dev":
            z.setdefault("mock_password", _DEFAULT_MOCK_PASSWORD)
        else:
            g = z.get("github")
            assert (
                g and g.get("client_id") and g.get("client_secret")
            ), "jupyter.github={} client_id/secret not set".format(g)

    def _enable_docker(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        z = self.j2_ctx[self.name]
        systemd.docker_unit_enable(
            self,
            self.j2_ctx,
            image=docker_registry.absolute_image(self),
            run_u=z.run_u,
        )

    def _install_jupyterhub_db(self, z):
        pass

    def _jupyterhub_db(self):
        return self.__run_d

    def _network(self, z, jc):
        self._vhost(z, jc)
        self.buildt.require_component("network")
        nc = self.buildt.get_component("network")
        z.hub_ip = nc.ip_and_net_for_host(jc.rsconf_db.host)[0]

    def _rsdockerspawner(self, z):
        from rsconf.component import docker

        z.tls_d = self.__run_d.join(_DOCKER_TLS_SUBDIR)
        c = PKDict(
            port_base=z.setdefault("port_base", _DEFAULT_PORT_BASE),
            tls_dir=str(z.tls_d),
        )
        # POSIT: notebook_dir in
        # radiasoft/container-beamsim-jupyter/container-conf/build.sh
        # parameterize anyway, because matches above
        z.pksetdefault("volumes", PKDict)
        z.pksetdefault("user_groups", PKDict)
        z.docker_hosts = self._rsdockerspawner_hosts(z)
        c.volumes = self._rsdockerspawner_volumes(z)
        c.user_groups = z.user_groups
        c.pools = z.pools
        z.rsdockerspawner_cfg = pkjson.dump_pretty(c)

    def _rsdockerspawner_hosts(self, z):
        seen = PKDict(
            hosts=PKDict(),
            users=PKDict(),
        )
        for n, p in z.pools.items():
            for h in p["hosts"]:
                assert (
                    h not in seen.hosts
                ), "duplicate host={} in two pools {} and {}".format(
                    h,
                    n,
                    seen.hosts[h],
                )
                seen.hosts[h] = n
            if n == _DEFAULT_POOL:
                assert (
                    "user_groups" not in p
                ), "user_groups may not be specified for pool={}".format(n)
            else:
                for s in _users_for_groups(p.user_groups, "pool", n, z.user_groups):
                    if s == DEFAULT_USER_GROUP:
                        continue
                    assert (
                        s not in seen.users
                    ), "duplicate user={} in two pools {} and {}".format(
                        s,
                        n,
                        seen.hosts[s],
                    )
                    seen.users[s] = n
        return list(seen.hosts.keys())

    def _rsdockerspawner_volumes(self, z):
        return Volumes(
            z.volumes, z.user_groups, z.user_d, z.home_d
        ).rsdockerspawner_cfg()

    def _vhost(self, z, jc):
        z.vhost = jc.jupyterhub.vhosts[jc.rsconf_db.host]


class Volume(PKDict):
    """Represents a volume to mount

    Args:
        mount (str): mount point in guest
        bind (str): host path to mount
        read_only (bool): true if read only
    """

    pass


class Volumes:
    """Represents and manipulates parsed volume config

    Example config represented as YAML::

        volumes:
           /home/vagrant/jupyter/StaffScratch:
               bind: /scratch-on-host
               ro: [ staff ]
           /home/vagrant/jupyter/StaffScratch/{username}:
               bind: /scratch-on-host/{username}
               rw: [ staff ]
         user_groups:
           staff: [ larry, moe, curly, laurel, hardy ]
           stooges: [ larry, moe, curly ]


    Will add the `host_home_d` to `guest_home_d` binding if not
    included already in `volumes`.

    Args:
        volumes (PKDict): map of mounts to bind, mode (see example)
        user_groups (PKDict): map of group name to user list (see example)
        host_home_d (py.path): root of user directories (e.g. /srv/jupyterhub/user)
        guest_home_d (py.path): guest users's home directory (e.g. /home/vagrant)
    """

    def __init__(self, volumes, user_groups, host_home_d, guest_home_d):
        def _cfg_to_list():
            res = []
            for n, v in self._cfg.items():
                res.append(
                    PKDict(
                        mount=n,
                        bind=v.bind,
                        rw=_users(v.mode.rw, n),
                        ro=_users(v.mode.ro, n),
                    )
                )
            return res

        def _default_mode():
            return PKDict(rw=[DEFAULT_USER_GROUP], ro=[])

        def _default_volume(res):
            x = str(host_home_d.join("{username}"))
            if x not in res:
                res[x] = PKDict(
                    bind=str(guest_home_d.join("jupyter")),
                    mode=_default_mode(),
                )
            return res

        def _normalize_and_default():
            res = PKDict()
            for n, v in volumes.items():
                try:
                    if not isinstance(v, dict):
                        x = PKDict(bind=v)
                    else:
                        assert "bind" in v, f"bind must be specified in volume={n}: {v}"
                        x = copy.deepcopy(v)
                        x.pksetdefault(mode=_default_mode)
                        x.mode.pksetdefault(rw=list)
                        x.mode.pksetdefault(ro=list)
                    res[n] = x
                except Exception:
                    pkdlog("volume={} config={}", n, v)
                    raise
            return _default_volume(res)

        def _users(groups, mount):
            if not groups:
                return set()
            return _users_for_groups(groups, "volume", mount, user_groups)

        self._cfg = _normalize_and_default()
        self._list = _cfg_to_list()

    def for_user_sorted_by_mount(self, user):
        """Find volumes matching user

        Args:
            user (str): matches jupyterhub name
        Returns:
            list: Volume instances in mount sorted order
        """

        def _fmt(path):
            return path.format(username=user)

        res = PKDict()
        for v in self._list:
            if n in res:
                # These loops are in precedence order
                continue
            # user overrides _EVERYBODY
            for n in user, _EVERYBODY:
                # rw overrides ro
                for m in "rw", "ro":
                    if n in v[m]:
                        res[v.mount] = Volume(
                            mount=_fmt(v.mount), bind=_fmt(v.bind), read_only=m == "ro"
                        )
        return sorted(res.values(), key=lambda x: x.mount)

    def rsdockerspawner_cfg(self):
        """Normalized rsdockerspawner config

        Returns:
            PKDict: ``volumes`` value of rsdockerspawner config
        """
        return self._cfg


def _users_for_groups(groups, category, key, user_groups):
    res = set()
    for g in groups:
        if g == DEFAULT_USER_GROUP:
            assert (
                len(groups) == 1
            ), f"group={DEFAULT_USER_GROUP} may be only group in user_groups={user_groups} in {category}={key}"
            return [DEFAULT_USER_GROUP]
        assert g in user_groups, f"user_group={g} not found for {category}={key}"
        res = res.union(user_groups[g])
    return res


def _list_to_str(v):
    return "'" + "','".join(v) + "'"
