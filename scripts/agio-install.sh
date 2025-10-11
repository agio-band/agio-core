#!/usr/bin/env bash

venv_dir=~/.config/agio/default-env
mkdir -p $venv_dir 

pyexec=$(which python3 2>/dev/null)

if [[ -z "$pyexec" ]]; then
    echo "Error: python3 not found in PATH" >&2
    exit 1
fi

py_version=$($pyexec -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Use Python Version: $py_version"

if ! command -v git >/dev/null 2>&1; then
    echo "Error: Git not installed!"
    echo "Use next command to install it:"
    echo "  sudo apt-get install git -y"
    exit 1
fi
echo "Creating venv: $venv_dir"
rm -rf $venv_dir
$pyexec -m venv $venv_dir
echo "Update PIP..."
$venv_dir/bin/python -m pip install -U pip  >/dev/null

if (( $(echo "$py_version < 3.11" | bc -l) )); then
    echo "Install tomllib..."

    $venv_dir/bin/python -m pip install tomli >/dev/null
fi
echo "Install agio.core..."
$venv_dir/bin/python -m pip install -q git+https://github.com/agio-band/agio-core.git  >/dev/null 2>&1

bin_file=~/.local/bin/agio
if [[ -e "$bin_file" ]]; then
    if ! rm -rf "$bin_file"; then
        echo "Update binary error"
        exit 1
    fi
fi

ln -s $venv_dir/bin/agio $bin_file
echo "Installation complete!"
echo "Command 'agio' is available now for user ${USER}"