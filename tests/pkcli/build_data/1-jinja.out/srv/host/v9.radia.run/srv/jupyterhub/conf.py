# -*-python-*-
from rsdockerspawner import rsdockerspawner
import binascii

c.Authenticator.admin_users = set(['vagrant'])
import oauthenticator
c.JupyterHub.authenticator_class = oauthenticator.GitHubOAuthenticator
c.GitHubOAuthenticator.client_id = 'xyzzy'
c.GitHubOAuthenticator.client_secret = 'big-secret'
c.GitHubOAuthenticator.oauth_callback_url = 'https://jupyter.v9.radia.run/hub/oauth_callback'
c.JupyterHub.cleanup_servers = False
#TODO(robnagler) DEPRECATED remove after prod release
c.JupyterHub.confirm_no_ssl = True
c.JupyterHub.cookie_secret = binascii.a2b_hex('7cca36e11924ee491289c16db96751a5069fb838b4e68be34a62a4c1bbe37b37')
c.ConfigurableHTTPProxy.api_url = 'http://10.10.10.90:8113'
c.JupyterHub.hub_ip = '10.10.10.90'
c.JupyterHub.ip = '10.10.10.90'
c.JupyterHub.port = 8110
c.JupyterHub.hub_port = 7913
c.JupyterHub.template_vars = {}
c.JupyterHub.upgrade_db = True
c.ConfigurableHTTPProxy.auth_token = 'a324e39d4ccc7ec21400def54ad25d3007282d8f9be7fdb731c327008cee258d'
c.DockerSpawner.http_timeout = 30
# https://github.com/radiasoft/rsconf/issues/54
c.DockerSpawner.image_whitelist = []
c.DockerSpawner.image = 'radiasoft/custom-jupyter:latest'
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = 'host'
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
    "tls_dir": "/srv/jupyterhub/docker_tls",
    "user_groups": {},
    "volumes": {
        "/srv/jupyterhub/user/{username}": {
            "bind": "/home/vagrant/jupyter"
        }
    }
}
'''
c.JupyterHub.spawner_class = rsdockerspawner.RSDockerSpawner
if hasattr(rsdockerspawner.RSDockerSpawner, 'sirepo_template_dir'):
    c.JupyterHub.template_paths = [rsdockerspawner.RSDockerSpawner.sirepo_template_dir()]
#c.Application.log_level = 'DEBUG'
# Might not want this, but for now it's useful to see everything
#c.JupyterHub.debug_db = True
#c.ConfigurableHTTPProxy.debug = True
#c.JupyterHub.log_level = 'DEBUG'
#c.LocalProcessSpawner.debug = True
#c.Spawner.debug = True
