<#
.SYNOPSIS
Installs and configures the agio.core environment using uv.
.DESCRIPTION
This script performs the following steps:
1. Checks for and installs UV package manager if missing.
2. Checks for Git installation.
3. Creates a default virtual environment (.venv) using Python 3.11.
4. Installs agio.core from a Git repository into the virtual environment.
5. Creates an 'agio.cmd' wrapper in a user's local application path for easy execution.
.PARAMETER QuietMode
If present, enables quiet mode (not fully implemented in this version, but passed as argument to uv).
#>
param(
    [Parameter(Position=0)]
    [string]$QuietMode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Set the QUIET_MODE variable based on the argument
$QUIET_MODE_ARG = ""
if ($QuietMode -eq "-q") {
    $QUIET_MODE_ARG = "--quiet"
}

## Install UV if not exists
Write-Host "Checking for UV and attempting to install if missing..."

try {
    $uv_path = (Get-Command uv -ErrorAction Stop).Path
    Write-Host "UV found at: $uv_path"
}
catch {
    Write-Host "UV not found. Installing UV globally via PowerShell..."

    try {
        # Run UV installation
        Invoke-Expression (Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1)
        Start-Sleep -Seconds 1
        try {
            $uv_path = (Get-Command uv -ErrorAction Stop).Path
            Write-Host "UV installed successfully."
        }
        catch {
            Write-Host "Error: UV installed, but not found in PATH. Please restart your PowerShell session."
            Exit 1
        }
    }
    catch {
        Write-Host "Error: Failed to install UV. Check PowerShell execution policy or connectivity."
        Exit 1
    }
}

## Git Check
Write-Host "Checking for Git..."
try {
    $git_path = (Get-Command git -ErrorAction Stop).Path
    Write-Host "Git found at: $git_path"
}
catch {
    Write-Host "Error: Git not installed!"
    Write-Host "Please install Git from https://git-scm.com/download/win and ensure it's in your PATH."
    Exit 1
}

## Constants and Directories
$AGIO_CONFIG_DIR = Join-Path -Path $env:APPDATA -ChildPath "agio\default-env"
$PYTHON_VERSION = "3.11"
$VENV_DIR = Join-Path -Path $AGIO_CONFIG_DIR -ChildPath ".venv"

Write-Host "Install to $AGIO_CONFIG_DIR"

## 4. Create venv using Python 3.11
Write-Host "Target Python Version: $PYTHON_VERSION"
Write-Host "Creating project directory: $AGIO_CONFIG_DIR"

# Remove directory if it exists
if (Test-Path -Path $AGIO_CONFIG_DIR) {
    Remove-Item -Path $AGIO_CONFIG_DIR -Recurse -Force
}

# Create venv directory
New-Item -Path $AGIO_CONFIG_DIR -ItemType Directory | Out-Null
Set-Location -Path $AGIO_CONFIG_DIR
Write-Host "Initializing uv project..."
uv init --bare
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to initialize UV project. Exit code: $LASTEXITCODE"
    Exit 1
}

Write-Host "Creating venv: $VENV_DIR"
uv venv --python $PYTHON_VERSION
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to create venv with Python $PYTHON_VERSION."
    Write-Host "Check if Python $PYTHON_VERSION is installed and in PATH."
    Exit 1
}

## Install agio.core
Write-Host "Installing agio.core..."
uv pip install $QUIET_MODE_ARG git+https://github.com/agio-band/agio-core.git
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install agio.core. Exit code: $LASTEXITCODE"
    Exit 1
}
Write-Host "agio.core installed."

## 6. Create agio shortcut

$BIN_DIR = Join-Path -Path $env:USERPROFILE -ChildPath "AppData\Local\Microsoft\WindowsApps"
$AGIO_CMD_WRAPPER = Join-Path -Path $BIN_DIR -ChildPath "agio.cmd"

Write-Host "Creating agio wrapper in $BIN_DIR..."
$AGIO_EXE = Join-Path -Path $VENV_DIR -ChildPath "Scripts\agio.exe"

# Delete old if exists
if (Test-Path -Path $AGIO_CMD_WRAPPER) {
    Remove-Item -Path $AGIO_CMD_WRAPPER
}

# 2. Create shortcut agio.cmd
$WrapperContent = @"
@echo off
CHCP 1251 > nul
CALL "$AGIO_EXE" %*
"@

# Use encoding Windows-1251 (Code Page 1251)
[System.IO.File]::WriteAllText($AGIO_CMD_WRAPPER, $WrapperContent, [System.Text.Encoding]::GetEncoding(1251))

Write-Host ""
Write-Host "Installation complete!"
Write-Host "Command 'agio' is available now for user $env:USERNAME."
Write-Host ""

Exit 0