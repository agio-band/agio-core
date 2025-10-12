param(
    [Parameter(Position=0)]
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$QUIET_MODE = $Quiet.IsPresent

$CONFIG_ROOT = Join-Path -Path $env:APPDATA -ChildPath "agio"
$WORKSPACES_DIR = Join-Path -Path $CONFIG_ROOT -ChildPath "workspaces"
$VENV_DIR = Join-Path -Path $CONFIG_ROOT -ChildPath "default-env"
$BIN_DIR = Join-Path -Path $env:USERPROFILE -ChildPath "AppData\Local\Microsoft\WindowsApps"
$BIN_FILE = Join-Path -Path $BIN_DIR -ChildPath "agio.cmd"


function Confirm-Deletion {
    if ($QUIET_MODE) {
        return $true
    }
    return $PSCmdlet.ShouldContinue("Uninstallation", "Are you sure you want to uninstall agio files?")
}

if (Confirm-Deletion) {
    Write-Host "Uninstalling agio..."

    # Delete workspaces
    Write-Host "Removing workspaces: $WORKSPACES_DIR"
    if (Test-Path -Path $WORKSPACES_DIR) {
        try {
            Remove-Item -Path $WORKSPACES_DIR -Recurse -Force
        }
        catch {
            Write-Warning "Failed to remove workspaces: $($_.Exception.Message)"
        }
    }

    # Delete default env
    Write-Host "Removing default venv: $VENV_DIR"
    if (Test-Path -Path $VENV_DIR) {
        try {
            Remove-Item -Path $VENV_DIR -Recurse -Force
        }
        catch {
            Write-Warning "Failed to remove default venv: $($_.Exception.Message)"
        }
    }

    # Delete shortcut
    Write-Host "Removing agio binary wrapper: $BIN_FILE"
    if (Test-Path -Path $BIN_FILE) {
        try {
            Remove-Item -Path $BIN_FILE -Force
        }
        catch {
            Write-Warning "Failed to remove agio wrapper: $($_.Exception.Message)"
        }
    }

    Write-Host ""
    Write-Host "Uninstall completed."

} else {
    Write-Host "Canceled"
    Exit 0
}