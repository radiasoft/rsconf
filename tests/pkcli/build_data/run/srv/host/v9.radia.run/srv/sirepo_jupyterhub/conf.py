# -*-python-*-
from rsdockerspawner import rsdockerspawner
import binascii
import jupyterhub.spawner
import sirepo.jupyterhub


c.Authenticator.admin_users = set(['vagrant'])

# ip/port for the http_proxy. Nginx will proxy requests to this.
c.JupyterHub.ip = '10.10.10.90'
c.JupyterHub.port = 8111

# url for hub api access to proxy
c.ConfigurableHTTPProxy.api_url = 'http://10.10.10.90:8112'

# ip/port hub binds to. User servers and proxy will use this to
# communicate with the hub.
c.JupyterHub.hub_ip = '10.10.10.90'
c.JupyterHub.hub_port = 7914

c.ConfigurableHTTPProxy.auth_token = '661edb7c18f67805ca4b1b4460e3dcf9a2332ba9d80592f151b88e3be8ff5722'
c.DockerSpawner.http_timeout = 30
c.DockerSpawner.image = 'v3.radia.run:5000/radiasoft/beamsim-jupyter:dev'
# https://github.com/radiasoft/rsconf/issues/54
c.DockerSpawner.image_whitelist = []
c.DockerSpawner.network_name = 'host'
c.DockerSpawner.use_internal_ip = True
c.JupyterHub.authenticator_class = sirepo.jupyterhub.Authenticator
c.JupyterHub.base_url = '/jupyter'
c.JupyterHub.cleanup_servers = False
c.JupyterHub.cookie_secret = binascii.a2b_hex('f85a8b6f76b0e88b93f4dc0a835f9978d3e1d684732b121a5ad48257e6c9a38c')
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
            "bind": "/home/vagrant/jupyter"
        }
    }
}
'''
