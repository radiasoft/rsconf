#!/bin/bash
bop_rsconf_component() {
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/bop_common.conf' 'c1d99294b29bf45941e00ac75613b2e2'
bop_main
}
#!/bin/bash

bop_facade_setup() {
    local src_d=$1
    local dst_d=$2
    local logo_uri=$3
    local x src dst
    for x in b i f; do
        if [[ -e $src_d/$x && ! -L $dst_d/$x ]]; then
            ln -s -r "$src_d/$x" "$dst_d/$x"
        fi
    done
    for x in png gif jpg; do
        src="$src_d/i/logo.$x"
        if [[ ! -e $src ]]; then
            continue
        fi
        dst="$dst_d/$logo_uri"
        if [[ ! -e $dst || $src -nt $dst ]]; then
            convert "$src" "$dst"
            chmod 644 "$dst"
        fi
        return
    done
    install_err "$src: facade logo for maintenance not found"
}

bop_main() {
    bop_facade_setup '/var/www/facades/petshop/plain' '/srv/petshop/srv/petshop' '/m/logo.png'
    bop_facade_setup '/var/www/facades/beforeother/plain' '/srv/petshop/srv/beforeother' '/m/logo.png'
    bop_facade_setup '/var/www/facades/m-petshop/plain' '/srv/petshop/srv/m-petshop' '/m/logo.png'
    bop_facade_setup '/var/www/facades/other/plain' '/srv/petshop/srv/other' '/m/logo.png'
    bop_facade_setup '/var/www/facades/requiresecure/plain' '/srv/petshop/srv/requiresecure' '/m/logo.png'

}

