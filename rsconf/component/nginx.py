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

_CONF_D = _CONF_ROOT_D.join('conf.d')

_DEFAULT_ROOT = pkio.py_path('/usr/share/nginx/html')

_GLOBAL_CONF = _CONF_ROOT_D.join('nginx.conf')

_DEFAULT_ERROR_PAGES = '''
    error_page 404 /404.html;
    location = /40x.html { }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html { }
'''

def install_vhost(compt):
    j2_ctx = pkcollections.Dict(compt.hdb)
    j2_ctx.update(
        nginx_default_error_pages=_DEFAULT_ERROR_PAGES,
        nginx_default_root=_DEFAULT_ROOT,
    )
    compt.install_access(mode='400', owner=compt.hdb.rsconf_db_root_u)
    kc = compt.install_tls_key_and_crt(compt.hdb[compt.name + '_nginx_vhost'], _CONF_D)
    j2_ctx.nginx_tls_crt = kc.crt
    j2_ctx.nginx_tls_key = kc.key
    compt.install_resource(
        compt.name + '/nginx.conf',
        j2_ctx,
        _CONF_D.join(compt.name + '.conf'),
    )


class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        self.append_root_bash('rsconf_yum_install nginx')
        systemd.unit_prepare(self, _CONF_ROOT_D)
        j2_ctx = pkcollections.Dict(self.hdb)
        self.install_access(mode='400', owner=self.hdb.rsconf_db_root_u)
        self.install_resource('nginx/global.conf', j2_ctx, _GLOBAL_CONF)
        systemd.unit_enable(self)