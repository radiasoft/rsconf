#!/bin/bash
#
# Creates $rpm_name-<date>.<time>-1.rpm
#
set -euo pipefail

empty_rpm_main() {
    declare rpm_name=$1
    declare t=$HOME/rpmbuild
    mkdir -p "$t"/{RPMS,BUILD,BUILDROOT,SPECS,tmp}
    if [[ ! -r "$HOME"/.rpmmacros ]]; then
        cat <<EOF > "$HOME"/.rpmmacros
%_topdir   $t
%_tmppath  %{_topdir}/tmp
EOF
    fi
    declare s=$t/SPECS/$rpm_name.spec
    declare r=$t/BUILDROOT
    cat <<EOF > "$s"
Summary: $rpm_name
Name: $rpm_name
Version: $(date +%Y%m%d.%H%M%S)
Release: 1
License: Apache
BuildRoot: $r

%description
empty

%prep

%build

%install
rm -rf "$r"
mkdir "$r"
date > "$r/$rpm_name"

%clean
rm -rf "$r"

%files
%defattr(-,root,root)
/$rpm_name
EOF
    rpmbuild --buildroot "$r" -bb "$s"
    mv "$t/RPMS/x86_64/$rpm_name"*.rpm .
    echo "$rpm_name"*rpm
}

empty_rpm_main "$@"
