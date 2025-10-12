#!/usr/bin/env bash

set -e
QUIET_MODE="NO"
if [[ "$1" == "-q" ]]; then
    QUIET_MODE="YES"
fi

confirm_deletion() {
    if [[ "$QUIET_MODE" == "YES" ]]; then
        return 0
    fi
    read -r -p "Uninstall agio files (Y/n)? " response
    case "$response" in
        [yY][eE][sS]|[yY]|"")
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

if confirm_deletion; then
    echo "Uninstalling agio..."

    # 1. workspaces
    echo "Remove workspaces..."
    rm -fr "$HOME/.config/agio/workspaces"

    # 2. default env
    echo "Remove default venv..."
    rm -fr "$HOME/.config/agio/default-env"

    # 3. remove binary

    bin_file="$HOME/.local/bin/agio"
    if [[ -L "$bin_file" ]] || [[ -f "$bin_file" ]]; then
        echo "Remove agio binary $bin_file..."
        rm -f "$bin_file"
    fi

    echo "Uninstall completed."
else
    echo "Canceled"
    exit 0
fi