#!/bin/bash
logrotate_rsconf_component() {
rsconf_service_prepare 'logrotate.timer' '/etc/systemd/system/logrotate.service' '/etc/systemd/system/logrotate.timer' '/srv/logrotate'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/logrotate'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/logrotate/start' '0ee6bd9140a1e789bbac953e68a99916'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/logrotate.timer' '69521a1cb99040ac1bba5a0c7e5f24f5'
rsconf_install_file '/etc/systemd/system/logrotate.service' '17619e00593404a417203090aa6721ee'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/logrotate/run' 'f206f926ebf120cf6cdc65455dd16bef'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/logrotate.conf' 'c59f3376adf6ef244541b8ae596cc304'
logrotate_main
}
#!/bin/bash

logrotate_main() {
    # We use a systemd timer so can have output in the journal, and not emailed (anacron requires email)
    rm -f /etc/cron.daily/logrotate
    # We have our own run directory
    if [[ ! -L /var/lib/logrotate ]]; then
        rm -rf /var/lib/logrotate
        ln -r -s '/srv/logrotate' /var/lib/logrotate
    fi
    # These don't have sensible defaults. See our logrotate.conf.jinja
    rm -f /etc/logrotate.d/{bootlog,yum}
    if [[ -e /etc/logrotate.d/nginx ]]; then
        # This retention policy should be global
        rsconf_edit_no_change_res=0 rsconf_edit /etc/logrotate.d/nginx '#rotate' \
            's/\brotate/#rotate/'
    fi
    # Must exist for logrotate.conf.jinja to export and rotate the journal
    if [[ ! -e /var/log/journal.export ]]; then
        install -m 600 -o root -g root /dev/null /var/log/journal.export
    fi
    # Fix up audit.log.1,2,etc.
    local i f x
    local b=/var/log/audit/audit.log
    for i in 1 2 3 4; do
        f=$b.$i
        if [[ -r $f ]]; then
            x=$b-$(date +%Y%m%d -r "$f").xz
            xz -c < "$f" > "$x"
            touch -r "$f" "$x"
            rm -f "$f"
        fi
    done
    # Files with gz or not compressed, need to be xz compressed
    x='*-201[789][01][0-9][0-3][0-9]'
    for f in $(find /var/log -name "$x.gz" -o -name "$x"); do
        if [[ $f =~ gz$ ]]; then
            gunzip "$f"
            f=${f%.gz}
        fi
        xz "$f"
    done
}

