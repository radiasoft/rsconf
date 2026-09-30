#!/bin/bash
postfix_rsconf_component() {
rsconf_yum_install postfix procmail cyrus-sasl cyrus-sasl-plain postfix-lmdb
rsconf_service_prepare 'postfix' '/etc/systemd/system/postfix.service' '/etc/systemd/system/postfix.service.d' '/etc/postfix'
rsconf_install_access '440' 'root' 'mail'
rsconf_install_file '/etc/postfix/sender_access' '0b4502ada3610b0add93020a51164241'
rsconf_install_file '/etc/postfix/sasl_password' '0f0f3e032c766fecbf94d6b541745d54'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/postfix/v5.radia.run.key' '9cf4b3a792f1264ed6e81b09d03a5032'
rsconf_install_file '/etc/postfix/v5.radia.run.crt' '30806f8c18b86bce0169f26a19b529e2'
rsconf_install_access '644' 'root' 'root'
rsconf_install_file '/etc/postfix/main.cf' '5c2dc5e082616efd931e62637225a07a'
rsconf_install_file '/etc/postfix/master.cf' '818cf40a11671ed39d7097216d811000'
rsconf_install_file '/etc/aliases' '505977dfd514ab835c60dacf40535cd1'
postfix_main
rsconf_service_restart_at_end 'postfix'
}
#!/bin/bash

postfix_main() {
    # never hurts
    newaliases
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

