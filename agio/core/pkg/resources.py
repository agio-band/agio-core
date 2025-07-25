import os
from pathlib import Path
from functools import lru_cache

from agio.core.utils import config


@lru_cache
def get_resources_dirs():
    from agio.core import package_hub

    resource_dir_list = [
        Path(__file__).parent,
    ]
    # from env

    from_env = config.WS.RESOURCES_DIR
    if from_env:
        resource_dir_list.extend([Path(path) for path in from_env.split(os.pathsep)])
    # from packages
    for pkg in package_hub.iter_packages():
        resource_dir_list.append(pkg.get_resource_dir())
    return resource_dir_list


def get_res(resource_name: str) -> str | None:
    for path in get_resources_dirs():
        full_path = Path(path, resource_name).resolve()
        if full_path.exists():
            return full_path.as_posix()

