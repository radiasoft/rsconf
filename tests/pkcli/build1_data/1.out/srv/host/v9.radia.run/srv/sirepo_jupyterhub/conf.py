# -*-python-*-
from rsdockerspawner import rsdockerspawner
import binascii
import jupyterhub.spawner
import sirepo.jupyterhub


c.Authenticator.admin_users = set(['vagrant'])
c.Authenticator.allow_all = True

# url for hub api access to proxy
c.ConfigurableHTTPProxy.api_url = 'http://10.10.10.90:8112'
c.ConfigurableHTTPProxy.pid_file = '/tmp/jupyter-proxy.pid'
c.ConfigurableHTTPProxy.auth_token = 'f7e67a2628f79056ac596318a88d2fabd4a955f9f8a857d05920a77336d65f98'

c.DockerSpawner.http_timeout = 30
c.DockerSpawner.image = 'v3.radia.run:5000/radiasoft/beamsim-jupyter:dev'
# https://github.com/radiasoft/rsconf/issues/54
c.DockerSpawner.allowed_images = []
c.DockerSpawner.network_name = 'host'
c.DockerSpawner.use_internal_ip = True

# ip/port for the http_proxy. Nginx will proxy requests to this.
c.JupyterHub.ip = '10.10.10.90'
c.JupyterHub.port = 8111
# ip/port hub binds to. User servers and proxy will use this to
# communicate with the hub.
c.JupyterHub.hub_ip = '10.10.10.90'
c.JupyterHub.hub_port = 7914

c.JupyterHub.authenticator_class = sirepo.jupyterhub.SirepoAuthenticator
c.JupyterHub.base_url = '/jupyter'
c.JupyterHub.cleanup_servers = False
c.JupyterHub.cookie_secret = binascii.a2b_hex('1455aa08c52b0c0b284abc00ed2e68a89c79833c5eced879ad47f2c891ed1639')
c.JupyterHub.spawner_class = rsdockerspawner.RSDockerSpawner
c.JupyterHub.template_vars = {}
c.JupyterHub.upgrade_db = True

if hasattr(rsdockerspawner.RSDockerSpawner, 'sirepo_template_dir'):
    c.JupyterHub.template_paths = [rsdockerspawner.RSDockerSpawner.sirepo_template_dir()]
c.RSDockerSpawner.cfg = '''{
    "pools": {
        "everybody": {
            "cpu_limit": 0.5,
            "hosts": [
                "v9.radia.run"
            ],
            "mem_limit": "1G",
            "servers_per_host": 2
        }
    },
    "port_base": 8100,
    "tls_dir": "/srv/sirepo_jupyterhub/docker_tls",
    "user_groups": {},
    "volumes": {
        "/srv/jupyterhub/user/{username}": {
            "bind": "/home/vagrant/jupyter",
            "mode": {
                "ro": [],
                "rw": [
                    "everybody"
                ]
            }
        }
    }
}
'''

c.SirepoAuthenticator.sirepo_uri = 'https://sirepo.v4.radia.run'
