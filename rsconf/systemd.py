"""create systemd files

:copyright: Copyright (c) 2017-2023 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from pykern import pkconfig
from pykern import pkio
import datetime
import pytz
import re

_SYSTEMD_DIR = pkio.py_path("/etc/systemd/system")

# TODO(robnagler) when to download new version of docker container?
# TODO(robnagler) docker pull happens explicitly, probably


_DOCKER_SCRIPTS = ["env", "remove", "start", "stop"]


class _InstanceSpecBase(PKDict):
    pass


class InstanceSpec(_InstanceSpecBase):
    """For systemd instances, e.g. ``sirepo@.service``.
    Args:
        base (str): base name of service
        env_var (str): name of environment variable to cascade
        first_port (int): first instance
        last_port (int): last instance
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update(
            container_name=f"{self.base}-${self.env_var}",
            env_arg=f'--env {self.env_var}="${self.env_var}"',
            first_container_name=f"{self.base}-{self.first_port}",
            is_null=False,
            service_file=f"{self.base}@.service",
            service_name=f"{self.base}@{{{self.first_port}..{self.last_port}}}",
        )

    def exclude_exports(self, keys):
        return filter(lambda x: x != self.env_var, keys)


class _NullInstanceSpec(_InstanceSpecBase):
    """For units that don't have instances (the default)
    Args:
        env_var (str): name of environment variable to cascade
        first_port (int): first instance
        last_port (int): last instance
    """

    def __init__(self, base):
        super().__init__(
            base=base,
            container_name=base,
            env_arg="",
            env_var=None,
            first_container_name=base,
            first_port=None,
            is_null=True,
            last_port=None,
            service_file=f"{base}.service",
            service_name=base,
        )

    def exclude_exports(self, keys):
        return keys


def custom_unit_enable(
    compt,
    j2_ctx,
    after=None,
    run_u=None,
    resource_d=None,
    run_d_mode="700",
    run_group=None,
):
    """Must be last call"""
    if not resource_d:
        resource_d = compt.module_name
    z = j2_ctx.systemd
    z.update(
        after=_after(after),
        run_u=run_u or j2_ctx.rsconf_db.run_u,
    )
    z.run_group = run_group or z.run_u
    compt.install_access(mode=run_d_mode, owner=z.run_u, group=z.run_group)
    compt.install_directory(z.run_d)
    # pid_file has to be in a public directory that is writeable by run_u
    # "PID file /srv/petshop/petshop.pid not readable (yet?) after start."
    compt.install_access(mode="755")
    compt.install_access(mode="500")
    for s in z._scripts:
        if z.get(s):
            compt.install_resource(
                resource_d + "/" + s + ".sh",
                j2_ctx,
                z[s],
            )
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # These files should be 400, since there's no value in making them public.
    compt.install_access(mode="444", owner=j2_ctx.rsconf_db.root_u)
    compt.install_resource(
        "systemd/custom_unit",
        j2_ctx,
        z.service_f,
    )
    unit_enable(compt, j2_ctx)


def custom_unit_prepare(
    compt,
    j2_ctx,
    watch_files=(),
    instance_spec=None,
    scripts=("start",),
    docker_exec=None,
    is_docker=False,
):
    """Must be first call"""
    run_d = unit_run_d(j2_ctx, compt.name)
    unit_prepare(
        compt,
        j2_ctx,
        [run_d] + list(watch_files),
        instance_spec=instance_spec,
    )
    z = j2_ctx.systemd
    z.run_d = run_d
    z.is_timer = False
    z.is_docker = is_docker
    z.docker_exec = docker_exec
    _prepare_scripts(z, scripts)
    if z.instance_spec.is_null:
        # systemd creates RuntimeDirectory in /run see custom_unit.service
        z.runtime_d = pkio.py_path("/run").join(z.service_name)
        z.pid_file = z.runtime_d.join(z.service_name + ".pid")
    else:
        # Instances don't have pid_files. They are managed by systemd
        z.pkdel("pid_file")
        z.pkdel("runtime_d")
    return run_d


def docker_unit_enable(
    compt,
    j2_ctx,
    image,
    env=None,
    volumes=None,
    after=None,
    run_u=None,
    ports=None,
    static_files_gen="",
):
    """Must be last call"""
    from rsconf.component import docker_registry

    def _exports(instance_spec, env):
        return "\n".join(
            [
                f"export '{k}={env[k]}'"
                for k in instance_spec.exclude_exports(sorted(env.keys()))
            ],
        )

    def _extra_run_flags(instance_spec):
        c = z.pkunchecked_nested_get("extra_run_flags." + compt.module_name)
        if not c:
            return ""
        return " ".join([f"--{k}='{v}'" for k, v in c.items()])

    z = j2_ctx.systemd
    if env is None:
        env = PKDict()
    # Tested on CentOS 7, and it does have the localtime stat problem
    # https://blog.packagecloud.io/eng/2017/02/21/set-environment-variable-save-thousands-of-system-calls/
    env.pksetdefault(TZ=":/etc/localtime")
    z.update(
        after=_after(after),
        exports=_exports(z.instance_spec, env),
        extra_run_flags=_extra_run_flags(z.instance_spec),
        image=docker_registry.absolute_image(compt, j2_ctx, image),
        run_u=run_u or j2_ctx.rsconf_db.run_u,
    )
    volumes = _tuple_arg(volumes)
    run_d_in_volumes = False
    for v in volumes:
        if v[0] == z.run_d:
            run_d_in_volumes = True
    if not run_d_in_volumes:
        volumes.insert(0, (str(z.run_d), str(z.run_d)))
    z.volumes = _colon_format("-v", volumes)
    z.network = _colon_format("-p", _tuple_arg(ports))
    if not z.network:
        z.network = "--network=host"
    compt.install_access(mode="700", owner=z.run_u)
    compt.install_directory(z.run_d)
    compt.install_access(mode="500")
    for s in z._scripts:
        compt.install_resource("systemd/docker_" + s, j2_ctx, z[s])
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # These files should be 400, since there's no value in making them public.
    compt.install_access(mode="444", owner=j2_ctx.rsconf_db.root_u)
    if z.is_timer:
        assert z.instance_spec.is_null
        compt.install_resource(
            "systemd/timer_unit",
            j2_ctx,
            z.timer_f,
        )
    compt.install_resource("systemd/docker_unit", j2_ctx, z.service_f)
    if not docker_registry.image_is_local(compt, j2_ctx, z.image):
        compt.append_root_bash(
            f"rsconf_service_docker_pull '{z.image}' '{z.service_name}' '{z.instance_spec.first_container_name}' '{static_files_gen}'"
        )
    unit_enable(compt, j2_ctx)


def docker_unit_prepare(
    compt,
    j2_ctx,
    watch_files=(),
    instance_spec=None,
    docker_exec=None,
):
    """Must be first call"""
    return custom_unit_prepare(
        compt=compt,
        j2_ctx=j2_ctx,
        watch_files=watch_files,
        instance_spec=instance_spec,
        scripts=None,
        docker_exec=docker_exec,
        is_docker=True,
    )


def install_unit_override(compt, j2_ctx):
    d = j2_ctx.systemd.unit_override_d
    # systemd requires files be publicly writable
    compt.install_access(mode="755", owner=j2_ctx.rsconf_db.root_u)
    compt.install_directory(d)
    compt.install_access(mode="444")
    compt.install_resource(
        compt.module_name + "/unit_override.conf",
        j2_ctx,
        d.join("99-rsconf.conf"),
    )


def timer_enable(compt, j2_ctx=None, run_u=None):
    if j2_ctx is None:
        j2_ctx = compt.j2_ctx
    z = j2_ctx.systemd
    z.run_u = run_u or j2_ctx.rsconf_db.run_u
    compt.install_access(mode="700", owner=z.run_u)
    compt.install_directory(z.run_d)
    compt.install_access(mode="500")
    compt.install_resource(
        "systemd/timer_start",
        j2_ctx,
        z.timer_start_f,
    )
    compt.install_access(mode="444", owner=j2_ctx.rsconf_db.root_u)
    compt.install_resource(
        "systemd/timer_unit",
        j2_ctx,
        z.timer_f,
    )
    compt.install_resource(
        "systemd/timer_unit_service",
        j2_ctx,
        z.service_f,
    )
    unit_enable(compt, j2_ctx)


def timer_prepare(
    compt,
    j2_ctx,
    on_calendar,
    watch_files=(),
    timer_exec=None,
    service_name=None,
    docker_exec=None,
):
    """Must be first call"""
    # TODO(robnagler) need to merge with unit_prepare
    assert docker_exec or timer_exec
    n = service_name or compt.name
    tn = n + ".timer"
    run_d = unit_run_d(j2_ctx, n)
    z = j2_ctx.pksetdefault(systemd=PKDict).systemd
    z.pksetdefault(timezone="America/Denver")
    z.pkupdate(
        instance_spec=_NullInstanceSpec(n),
        is_timer=True,
        on_calendar=_on_calendar(on_calendar, z.timezone),
        run_d=run_d,
        docker_exec=docker_exec,
        is_docker=bool(docker_exec),
        service_f=_SYSTEMD_DIR.join(n + ".service"),
        service_name=n,
        timer_f=_SYSTEMD_DIR.join(tn),
        timer_name=tn,
        timer_start_f=run_d.join("start"),
    )
    if timer_exec:
        z.timer_exec = timer_exec
    compt.service_prepare(
        [z.service_f, z.timer_f, run_d] + list(watch_files),
        name=tn,
    )
    if z.docker_exec:
        _prepare_scripts(z, scripts=None)
    return run_d


def unit_enable(compt, j2_ctx):
    # rsconf.sh does the actual work of enabling
    # good to have the hook here for clarity
    pass


def unit_prepare(compt, j2_ctx, watch_files=(), instance_spec=None):
    """Must be first call"""
    z = j2_ctx.pksetdefault(systemd=PKDict).systemd
    z.instance_spec = instance_spec or _NullInstanceSpec(compt.name)
    z.service_name = z.instance_spec.service_name
    f = _SYSTEMD_DIR.join(z.instance_spec.service_file)
    d = pkio.py_path(str(f) + ".d")
    z.pkupdate(
        service_f=f,
        unit_override_d=d,
    )
    compt.service_prepare(
        [f, d] + list(watch_files),
        name=z.service_name,
    )


def unit_run_d(j2_ctx, unit_name):
    return j2_ctx.rsconf_db.host_run_d.join(unit_name)


def _after(values):
    if not values:
        return ""
    s = ".service"
    return " ".join(
        [(v if v.endswith(s) else v + s) for v in values],
    )


def _colon_format(flag, values):
    return " ".join(
        ["{} '{}'".format(flag, ":".join(x)) for x in values],
    )


def _on_calendar(value, tz, now=None):
    """Simulation systemd timezones

    On CentOS, systemd does not support time zones.
    This code will generate the correct on_calendar offset.

    NOTE: You have to rerun rsconf no DST changeover and
    push to all hosts.

    Args:
        value (str): format: ``DOW H:M``, ``D H:M``, ``H``, ``H:M``
        tz (str): Olson time zone (e.g. ``America/Denver``)
        now (datetime): for testing only
    Returns:
        str: on_calendar format: ``[DOW] *-*-[D] H:M:S``
    """
    if now is None:
        # for unit testing
        now = datetime.datetime.utcnow()
    x = str(value).split(" ")
    res = "*-*-*"
    d = None
    if len(x) == 2:
        d = x.pop(0)
        if d.isdigit():
            res = "*-*-" + d
        else:
            assert re.search(
                r"^\w{3}(?:-\w{3})?$", d
            ), "Only day or day of week for value={}".format(value)
            res = d + " " + res
    else:
        assert len(x) == 1, 'only "day h:m" and "h:m" for value={}'.format(value)
    x = x[0].split(":")
    h = x[0]
    if h == "*":
        assert len(x) == 2, "hour={} requires minutes value={}".format(value)
        m = x[1]
    else:
        z = -int(pytz.timezone(tz).utcoffset(now).total_seconds()) // 3600
        h = (int(h) + z) % 24
        if d is not None:
            # Mon-Fri 17:0 works in Denver but not later
            # so we don't handle other cases. Value has to end in
            # the same day except h=0 below or if d is not set (every day)
            assert h == 0 or h >= z, "hour={} ends after midnight for value={}".format(
                h, value
            )
        m = "0"
        if len(x) >= 2:
            assert len(x) == 2, "seconds not supported for value={}".format(value)
            # may be of the form 0/5
            m = x[1]
        if h == 0 and d is not None:
            assert m == "0"
            # special case midnight to work (see above about 17:0)
            h = 23
            m = "59"
    return res + " {}:{}:0".format(h, m)


def _prepare_scripts(z, scripts):
    z._scripts = (
        ((["cmd"] if z.docker_exec else []) + _DOCKER_SCRIPTS)
        if z.is_docker
        else list(scripts)
    )
    for s in z._scripts:
        z[s] = z.run_d.join(s)


def _tuple_arg(values):
    if not values:
        return []
    res = []
    for v in values:
        if not isinstance(v, (tuple, list)):
            v = (v, v)
        res.append([str(x) for x in v])
    return res
