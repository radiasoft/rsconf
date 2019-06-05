#!/bin/bash
build_image_base=centos:7
build_want_yum_update=1

build_as_run_user() {
    cd
    bivio_pyenv_2
    mkdir -p src/radiasoft
    cd src/radiasoft
    local f
    for f in pykern rsconf download; do
        git clone https://github.com/radiasoft/"$f"
        cd "$f"
        if [[ -r setup.py ]]; then
            pip install -e .
        fi
        cd ..
    done
}
