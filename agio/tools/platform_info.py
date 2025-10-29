import platform
import sys


def detect_platform() -> list[str]:
    system = platform.system().lower()
    python_version = f"py{sys.version_info.major}.{sys.version_info.minor}"

    if system == "windows":
        return [f"windows-{python_version}", "windows", python_version, ""]
    elif system == "linux":
        distro = platform.freedesktop_os_release().get("ID", "linux").lower()
        version_id = platform.freedesktop_os_release().get("VERSION_ID", "").replace(".", "")
        return [
            f"{distro}{version_id}-{python_version}",
            f"{distro}{version_id}",
            f"{distro}-{python_version}",
            distro,
            python_version,
            ""
        ]
    elif system == "darwin":
        return [f"macos-{python_version}", "macos", python_version, ""]
    else:
        return [python_version, ""]


def get_platform_variables() -> dict:
    """
    {"os_name": "ubuntu", "os_version": "2410", "python": "2.12"}
    """
    distro = platform.freedesktop_os_release().get("ID", "linux").lower()
    os_version = platform.release()
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    return {
        "os_name": distro,
        "os_version": os_version,
        "python": py_version,
    }
