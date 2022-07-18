#!/bin/bash
set -euo pipefail
base=$1
if [[ ! -d ~/rpmbuild/SPECS ]]; then
    echo 'You need to build a regular rpm first with build-perl-rpms.sh'
    exit 1
fi
t=$HOME/rpmbuild
s=$t/SPECS/$base.spec
r=$t/BUILDROOT
cat <<EOF > "$s"
Summary: $base
Name: $base
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
date > "$r/$base"

%clean
rm -rf "$r"

%files
%defattr(-,root,root)
/$base
EOF
rpmbuild --buildroot "$r" -bb "$s"
mv "$t/RPMS/x86_64/$base"*.rpm .
echo "$base"*rpm
