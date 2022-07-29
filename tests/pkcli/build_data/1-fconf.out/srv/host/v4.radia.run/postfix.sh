#!/bin/bash
postfix_rsconf_component() {
rsconf_yum_install postfix procmail cyrus-sasl cyrus-sasl-plain
rsconf_service_prepare 'postfix' '/etc/systemd/system/postfix.service' '/etc/systemd/system/postfix.service.d' '/etc/postfix'
rsconf_install_access '440' 'root' 'mail'
rsconf_install_file '/etc/postfix/sender_access'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/sasl2/smtpd-sasldb.conf' '7d9b2345cc4447364639bbd15af40f2e'
rsconf_install_access '440' 'root' 'mail'
rsconf_install_file '/etc/postfix/virtual_alias_domains' 'a313ba8c909e22c2b214d86899dced9a'
rsconf_install_file '/etc/postfix/virtual_alias' 'b2faad6e3da1032b986ac8ae7bb25fa2'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/postfix/star.v4.radia.run.key' '031805b0a7c2e0fd1330b0613f385ede'
rsconf_install_file '/etc/postfix/star.v4.radia.run.crt' '19cdea6247d259c6ffb2b36726ea297c'
rsconf_install_access '644' 'root' 'root'
rsconf_install_file '/etc/postfix/main.cf' 'f7ae38f241e0f1cd657387434f317ece'
rsconf_install_file '/etc/postfix/master.cf' '0a14355ea1a1ae57497775949f308c1b'
rsconf_install_file '/etc/aliases' '014c8aa0c7b0a320bb594911a1b4c908'
postfix_main
rsconf_service_restart_at_end 'postfix'
}
#!/bin/bash

postfix_main() {
        postfix_setup_sasl
    # never hurts
    newaliases
}

postfix_setup_sasl() {
    rm -f /etc/sasldb2.new
        echo 'eUSrgIFTRbgSizYlYeLq9yPEuFEZehwL' | saslpasswd2 -f /etc/sasldb2.new -c -p -u 'v3.radia.run' 'postfix'
        echo 'saslpass' | saslpasswd2 -f /etc/sasldb2.new -c -p -u 'v4.radia.run' 'test1'
    chown root:mail /etc/sasldb2.new
    chmod 640 /etc/sasldb2.new
    mv -f /etc/sasldb2.new /etc/sasldb2
}


# Testing email
true <<'EOF2'
/usr/sbin/sendmail fourem@petshop.v4.radia.run <<'EOF'
To: fourem@petshop.v4.radia.run
Subject: testing 123
From: vagrant+btest_btest_admin@v4.radia.run

test
EOF
EOF2

