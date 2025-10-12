#!/usr/bin/env bash

# Install uv
if ! command -v uv >/dev/null 2>&1; then
    echo "UV not found. Installing UV..."
    if command -v pipx >/dev/null 2>&1; then
        pipx install uv
    elif command -v curl >/dev/null 2>&1; then
        INSTALL_DIR="$HOME/.local/bin"
        mkdir -p "$INSTALL_DIR"

        curl -LsSf https://astral.sh/uv/install.sh | sh
        if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
            export PATH="$INSTALL_DIR:$PATH"
            echo "Added $INSTALL_DIR to PATH for this session."
        fi
    else
        echo "Error: Neither pipx nor curl found. Cannot install UV." >&2
        exit 1
    fi
    if ! command -v uv >/dev/null 2>&1; then
        echo "Error: Failed to install UV." >&2
        exit 1
    fi
    echo "UV installed successfully."
fi

# Check Git installed
if ! command -v git >/dev/null 2>&1; then
    echo "Error: Git not installed!"
    echo "Use the following command to install it:"
    echo "  sudo apt-get install git -y"
    exit 1
fi

# create default venv
venv_dir=~/.config/agio/default-env
python_version="3.11" # minimal required version
echo "Target Python Version: $python_version"
echo "Creating venv: $venv_dir with Python ${python_version}"
rm -rf "$venv_dir"
mkdir -p "$venv_dir"
cd "$venv_dir"
if ! uv init --bare; then
    echo "Error: Failed to create default venv project" >&2
    exit 1
fi
if ! uv venv --python "${python_version}"; then
    echo "Error: Failed to create venv with Python ${python_version}. Is Python ${python_version} installed and in PATH?" >&2
    exit 1
fi

# install core
echo "Installing agio.core..."
if ! uv pip install --quiet git+https://github.com/agio-band/agio-core.git; then
    echo "Error: Failed to install agio.core." >&2
    exit 1
fi
echo "agio.core installed."

# binary link
bin_file=~/.local/bin/agio

if [[ -e "$bin_file" ]]; then
    if ! rm -rf "$bin_file"; then
        echo "Update binary error: Could not remove old file." >&2
        exit 1
    fi
fi

ln -s "$venv_dir/.venv/bin/agio" "$bin_file"

echo "Installation complete!"
echo "Command 'agio' is available now for user ${USER} via the link in ~/.local/bin."