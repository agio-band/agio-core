#!/usr/bin/env bash

venv_dir=~/.agio/venv
mkdir -p $venv_dir 

pyexec=$(which python3 2>/dev/null)

if [[ -z "$pyexec" ]]; then
    echo "python3 not found in PATH" >&2
    exit 1
fi

$pyexec -m venv $venv_dir
$venv_dir/bin/python -m pip install -U pip
$venv_dir/bin/python -m pip install https://github.com/agio-band/agio-core.git

bin_file=~/.local/bin/agio
if [[ -e "$bin_file" ]]; then
    rm -rf "$bin_file"
    if [[ $? -eq 0 ]]; then
        echo .
    else
        echo "Update binary error"
        exit
    fi
fi
ln -s $venv_dir/bin/agio $bin_file
