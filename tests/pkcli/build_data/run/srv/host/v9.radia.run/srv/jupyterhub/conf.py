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
c.JupyterHub.cookie_secret = binascii.a2b_hex('9e3bcf1bdeca2e0012e6f21490a1374e879428b1c73a31f5196dc73cecf58a68')
c.ConfigurableHTTPProxy.api_url = 'http://10.10.10.90:8113'
c.JupyterHub.hub_ip = '10.10.10.90'
c.JupyterHub.ip = '10.10.10.90'
c.JupyterHub.port = 8110
c.JupyterHub.hub_port = 7913
c.JupyterHub.template_vars = {}
c.JupyterHub.upgrade_db = True
c.ConfigurableHTTPProxy.auth_token = '752b559cf03861e12a32fdc4f6bb7cd0c2b0d7d83a3c416a879f173b4b9e55de'
c.DockerSpawner.http_timeout = 30
# https://github.com/radiasoft/rsconf/issues/54
c.DockerSpawner.image_whitelist = []
c.DockerSpawner.image = 'v3.radia.run:5000/radiasoft/beamsim-jupyter:dev'
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
