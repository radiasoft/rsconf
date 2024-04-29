# -*-python-*-
from rsdockerspawner import rsdockerspawner
import binascii
import jupyterhub.spawner
import sirepo.jupyterhub


c.Authenticator.admin_users = set(['vagrant'])

# ip/port for the http_proxy. Nginx will proxy requests to this.
c.JupyterHub.ip = '10.10.10.40'
c.JupyterHub.port = 8111

# url for hub api access to proxy
c.ConfigurableHTTPProxy.api_url = 'http://10.10.10.40:8112'
c.ConfigurableHTTPProxy.pid_file = '/tmp/jupyter-proxy.pid'

# ip/port hub binds to. User servers and proxy will use this to
# communicate with the hub.
c.JupyterHub.hub_ip = '10.10.10.40'
c.JupyterHub.hub_port = 7914

c.ConfigurableHTTPProxy.auth_token = 'f7e67a2628f79056ac596318a88d2fabd4a955f9f8a857d05920a77336d65f98'
c.DockerSpawner.http_timeout = 30
c.DockerSpawner.image = 'v3.radia.run:5000/radiasoft/beamsim-jupyter:dev'
# https://github.com/radiasoft/rsconf/issues/54
c.DockerSpawner.image_whitelist = []
c.DockerSpawner.network_name = 'host'
c.DockerSpawner.use_internal_ip = True
c.JupyterHub.authenticator_class = sirepo.jupyterhub.SirepoAuthenticator
c.SirepoAuthenticator.sirepo_uri = 'https://sirepo.v4.radia.run'
c.JupyterHub.base_url = '/jupyter'
c.JupyterHub.cleanup_servers = False
c.JupyterHub.cookie_secret = binascii.a2b_hex('1455aa08c52b0c0b284abc00ed2e68a89c79833c5eced879ad47f2c891ed1639')
c.JupyterHub.spawner_class = rsdockerspawner.RSDockerSpawner
if hasattr(rsdockerspawner.RSDockerSpawner, 'sirepo_template_dir'):
    c.JupyterHub.template_paths = [rsdockerspawner.RSDockerSpawner.sirepo_template_dir()]
c.JupyterHub.template_vars = {}
c.JupyterHub.upgrade_db = True
c.RSDockerSpawner.cfg = '''{
    "pools": {
        "everybody": {
            "cpu_limit": 0.5,
            "hosts": [
                "v6.radia.run",
                "v5.radia.run"
            ],
            "mem_limit": "1G",
            "servers_per_host": 2,
            "shm_size": "256M"
        },
        "private": {
            "hosts": [
                "v4.radia.run"
            ],
            "servers_per_host": 1,
            "user_groups": [
                "private"
            ]
        }
    },
    "port_base": 8100,
    "tls_dir": "/srv/sirepo_jupyterhub/docker_tls",
    "user_groups": {
        "instructors": [
            "teach1"
        ],
        "private": [
            "vagrant"
        ]
    },
    "volumes": {
        "/srv/jupyterhub/user/Workshop": {
            "bind": "/home/vagrant/jupyter/Workshop",
            "mode": {
                "ro": [
                    "everybody"
                ],
                "rw": []
            }
        },
        "/srv/jupyterhub/user/Workshop/{username}": {
            "bind": "/home/vagrant/jupyter/Workshop/{username}",
            "mode": {
                "ro": [],
                "rw": [
                    "instructors"
                ]
            }
        },
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
