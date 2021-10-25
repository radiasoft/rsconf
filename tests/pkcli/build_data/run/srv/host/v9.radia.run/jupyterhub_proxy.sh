#!/bin/bash
jupyterhub_proxy_rsconf_component() {
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v4.radia.run.key' '959fa3b015c18886ed4a79e28d975aa2'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v4.radia.run.crt' '1da8781c10512dabaa85d4739bdd07cf'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v4.radia.run.conf' '4c835a522403e08edf72dd6d674801f3'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v9.radia.run.key' 'a54714e8b547c3deec0afb5149e42967'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v9.radia.run.crt' '4f70bd97f6779a4e3a91b9afaa34e04b'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v9.radia.run.conf' 'fd13dd33f456c4437c7d2bbb8781c51e'
}
