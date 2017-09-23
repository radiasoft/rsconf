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

_CONF_D = _CONF_ROOT_D.join(_CONF_D)

_DEFAULT_ROOT = pkio.py_path('/usr/share/nginx/html')

_DEFAULT_ERROR_PAGES = '''
    error_page 404 /404.html;
    location = /40x.html { }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html { }
'''

def install_virtual_host(compt):

    v = pkcollections.Dict(
        nginx_vhost=compt.hdb.get('{}_nginx_vhost'.format(compt.name)),
        nginx_default_root=_DEFAULT_ROOT,
        nginx_default_error_pages=_DEFAULT_ERROR_PAGES,
        nginx_ssl_crt=None,
        nginx_ssl_key=None,
    )
    b = self.hdb.get('{}_nginx_ssl_base'.format(compt.name))
    if b:
        self.install_access(mode='400', owner=self.hdb.root_u)
        for s in 'key', 'crt':
            ds = '.' + s
            x = _CONF_D.join(b) + ds
            v['nginx_ssl_' + s] = x
            #TODO(robnagler) if secret is already installed (MDC's)
            self.install_secret(x.basename, host_path=x, visibility='global')
    compt.install_resource(
        compt.name + '/nginx.conf',
        v,
        compt.name + '.conf',
    )


class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        systemd.unit_prepare(self, _CONF_ROOT_D)
        systemd.unit_enable(self)
        self.install_access(mode='400', owner=self.hdb.root_u)
        v = pkcollections.Dict(
            worker_processes=self.hdb.nginx_worker_processes,
        )
        compt.install_resource('nginx/nginx.conf', v, '{}/nginx.conf'.)
