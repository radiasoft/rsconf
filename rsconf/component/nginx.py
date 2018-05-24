# -*- coding: utf-8 -*-
u"""create nginx configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern import pkio

_CONF_ROOT_D = pkio.py_path('/etc/nginx')

CONF_D = _CONF_ROOT_D.join('conf.d')

_DEFAULT_ROOT = pkio.py_path('/usr/share/nginx/html')

_GLOBAL_CONF = _CONF_ROOT_D.join('nginx.conf')

_DEFAULT_ERROR_PAGES = '''
    error_page 404 /404.html;
    location = /40x.html { }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html { }
'''

_REDIRECT_FMT = '''
server {{
    listen {server_name}:80;
    server_name {server_name};
    return {redirect_status} {redirect_uri};
}}
'''

_REDIRECT_SSL_FMT = '''
server {{
    listen {server_name}:443;
    server_name {server_name};
    ssl_certificate {crt};
    ssl_certificate_key {key};
    return {redirect_status} {redirect_uri};
}}
'''


def install_auth(compt, filename, host_path, visibility, j2_ctx):
    compt.install_access(mode='440', owner=j2_ctx.rsconf_db.root_u, group='nginx')
    compt.install_secret_path(
        filename=filename,
        host_path=host_path,
        visibility=visibility,
    )


def install_vhost(compt, vhost, backend_host=None, backend_port=None, resource_d=None, j2_ctx=None):
    update_j2_ctx_and_install_access(compt, j2_ctx)
    kc = compt.install_tls_key_and_crt(vhost, CONF_D)
    j2_ctx.setdefault('nginx', pkcollections.Dict()).update(
        tls_crt=kc.crt,
        tls_key=kc.key,
        vhost=vhost,
        backend_host=backend_host,
        backend_port=backend_port,
    )
    compt.install_resource(
        (resource_d or compt.name) + '/nginx.conf',
        j2_ctx,
        CONF_D.join(vhost + '.conf'),
    )


def render_redirects(compt, j2_ctx, server_names, host_or_uri):
    kw = pkcollections.Dict(
        redirect_status=301,
    )
    if ':' in host_or_uri:
        kw.redirect_uri = host_or_uri
    else:
        s = 's' if compt.has_tls(j2_ctx, host_or_uri) else ''
        kw.redirect_uri = 'http{}://{}$request_uri'.format(s, host_or_uri)
    res = ''
    for s in server_names:
        kw.server_name = s
        res += _REDIRECT_FMT.format(**kw)
        if compt.has_tls(j2_ctx, s):
            kc = compt.install_tls_key_and_crt(s, CONF_D)
            kw.update(kc)
            res += _REDIRECT_SSL_FMT.format(**kw)
    return res


def update_j2_ctx_and_install_access(compt, j2_ctx):
    j2_ctx.setdefault('nginx', pkcollections.Dict()).update(
        default_error_pages=_DEFAULT_ERROR_PAGES,
        default_root=_DEFAULT_ROOT,
    )
    compt.install_access(mode='400', owner=j2_ctx.rsconf_db.root_u)


class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        self.buildt.require_component('base_all')
        self.append_root_bash('rsconf_yum_install nginx')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.nginx
        systemd.unit_prepare(self, j2_ctx, [_CONF_ROOT_D])
        self.install_access(mode='400', owner=self.hdb.rsconf_db.root_u)
        z.rendered_redirects = self._render_redirects(j2_ctx)
        if self.has_tls(j2_ctx, j2_ctx.rsconf_db.host):
            z.default_server_tls = self.install_tls_key_and_crt(
                j2_ctx.rsconf_db.host,
                CONF_D,
            )
        self.install_resource('nginx/global.conf', j2_ctx, _GLOBAL_CONF)
        systemd.unit_enable(self, j2_ctx)
        self.rsconf_service_restart_at_end()

    def _render_redirects(self, j2_ctx):
        res = ''
        redirects = j2_ctx.nginx.setdefault('redirects', [])
        for r in redirects:
            names = r.server_names
            if r.setdefault('want_www', False):
                names = sum([[s, 'www.' + s] for s in names], [])
            res += render_redirects(self, j2_ctx, names, r.host_or_uri)
        return res
