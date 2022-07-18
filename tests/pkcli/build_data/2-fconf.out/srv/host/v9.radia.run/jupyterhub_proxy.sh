#!/bin/bash
jupyterhub_proxy_rsconf_component() {
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v4.radia.run.key' 'e6563aaa738da91afd36bb3ded227a2a'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v4.radia.run.crt' '24e497053dd7bb3f778ffb8a349211a5'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v4.radia.run.conf' '4c835a522403e08edf72dd6d674801f3'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v9.radia.run.key' 'f1989e244a29d83b4ea7f32815aef28b'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v9.radia.run.crt' 'e48846a11f976523d94c0d8820ca740b'
rsconf_install_file '/etc/nginx/conf.d/jupyter.v9.radia.run.conf' 'fd13dd33f456c4437c7d2bbb8781c51e'
}
