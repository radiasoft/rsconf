#!/bin/bash
spamd_rsconf_component() {
rsconf_service_prepare 'spamd' '/etc/systemd/system/spamd.service' '/etc/systemd/system/spamd.service.d' '/srv/spamd' 'bivio-perl-dev.rpm' 'perl-Bivio-dev.rpm' '/etc/mail/spamassassin'
rsconf_install_access '755' 'vagrant' 'vagrant'
rsconf_install_directory '/etc/mail/spamassassin'
rsconf_install_directory '/run/spamd'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/spamd'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/spamd/log_postrotate' 'a0b319fdc030822f86a22cc322410f86'
rsconf_install_access '444' 'vagrant' 'vagrant'
rsconf_install_file '/etc/mail/spamassassin/spamc.conf' 'e8ebe857cf81d6cf9c39e070099bf0ec'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/logrotate.d/spamd' 'af1838eeec925f2e6dd89570732eb6d1'
spamd_main
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/spamd'
rsconf_install_access '755' 'vagrant' 'vagrant'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/spamd/start' 'da7947cd171a185b674f45aac09db5e1'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/spamd.service' 'f42ec8d8a0eaa370b3853dce2f5bc59f'
}
#!/bin/bash

spamd_main() {
    find /etc/mail/spamassassin/sa-update-keys ! -user root \
        | xargs --no-run-if-empty chown root:root
    # replace logrotate, which limits rotations and restarts spamd
    # sought.conf is removed, but Red Hat won't fix:
    # https://bugzilla.redhat.com/show_bug.cgi?id=1630362
    # See also https://github.com/biviosoftware/devops/issues/409
    rm -f /etc/logrotate.d/sa-update /etc/mail/spamassassin/channel.d/sought.conf
}

