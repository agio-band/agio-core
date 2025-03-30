import json
import subprocess


def get_site_packages_path(venv_python_path: str) -> str | None:
    try:
        result = subprocess.run(
            [venv_python_path, "-c", "import site, json; print(json.dumps(site.getsitepackages()))"],
            capture_output=True,
            text=True,
            check=True,
        )
        site_packages_list = json.loads(result.stdout.strip())
        return site_packages_list[0]
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        return None