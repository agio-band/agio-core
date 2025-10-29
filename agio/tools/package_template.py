import getpass
import re
import shutil
import sys
from pathlib import Path
from typing import Callable

from agio.tools.text_helpers import slugify, unslugify
from agio.core.workspaces.resources import get_res


def create_new_package(destination_path: str|Path,
                       name: str, python_package_name: str,  nice_name: str = None,
                       template_path: str = None, clear_target_dir: bool = False,
                       username: str = None, email: str = None, description: str = None,
                       **kwargs):
    py_name = python_package_name or validate_python_name(name)

    template_path = template_path or get_res('core/workspaces-template-default')
    if not template_path:
        raise RuntimeError('Template path is required')

    template_path = Path(template_path)

    full_path = Path(destination_path, name)
    if full_path.is_file():
        raise FileExistsError(f"File {full_path} already exists")
    if full_path.is_dir():
        if next(full_path.iterdir()):
            if not clear_target_dir:
                raise FileExistsError(f"Directory {full_path} is not empty")
            shutil.rmtree(full_path)
    context = dict(
        name=name,
        py_name=py_name,
        nice_name=nice_name or unslugify(name),
        username=username or getpass.getuser(),
        email=email or '',
        description=description or '',
    )
    return create_from_template(template_path, full_path, context, **kwargs)


def validate_python_name(name: str):
    py_name = slugify(name)
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", py_name):
        raise NameError(f"Package name '{name}' ({py_name}) is not valid name")
    if name in sys.stdlib_module_names:
        raise NameError(f"Package name '{py_name}' already used")
    return py_name


def validate_package_name(name: str):
    pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$", re.IGNORECASE)
    if not pattern.match(name):
        raise NameError(f"Package name '{name}' is not valid name")
    return name.lower()


def format_with_context(text: str, context: dict):
    def replace_value(match: re.Match):
        if match.group(1) not in context:
            raise KeyError(f"Key '{match.group(1)}' not found")
        value = context.get(match.group(1))
        return str(value)
    return re.sub(r'\{\{(.*?)}}', replace_value, text)


def create_from_template(src_pat: str|Path, target_path: str|Path, context: dict, file_callback: Callable = None, **kwargs):
    src_path = Path(src_pat)
    target_path = Path(target_path)
    target_path.mkdir(parents=True, exist_ok=True)
    for item in src_path.rglob('*'):
        trg_item = Path(
            target_path,
            format_with_context(item.relative_to(src_path).as_posix(), {**context, **kwargs}))
        if file_callback:
            file_callback(item)
        if item.is_dir():
            trg_item.mkdir(parents=True, exist_ok=True)
        else:
            data = item.read_text(encoding='utf-8')
            new_data = format_with_context(data, context)
            trg_item.write_text(new_data)
    return target_path.as_posix()
