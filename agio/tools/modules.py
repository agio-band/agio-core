import ast
import importlib.util
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


def import_module_by_path(path: str, name: str = None):
    spec = importlib.util.spec_from_file_location(name or "module", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def get_object_dot_path(obj: Any) -> str:
    """Return full dotted path of an object."""
    module_name = getattr(obj, '__module__', None)
    if hasattr(obj, '__qualname__'):
        obj_name = obj.__qualname__
    elif hasattr(obj, '__name__'):
        obj_name = obj.__name__
    else:
        raise TypeError(f"Object {type(obj)} is not a named element of module.")
    if module_name == 'builtins' or module_name is None:
        return obj_name
    return f"{module_name}.{obj_name}"


def import_object_by_dotted_path(dotted_path: str, object_name: str = None) -> type:
    """
    Import and return object inside module by dotted path.
    Path example: "my_module.my_submodule.MyClass"
    """
    if not object_name:
        dotted_path, object_name = dotted_path.rsplit('.', 1)
    module = importlib.import_module(dotted_path)
    return getattr(module, object_name)


def get_class_attrib_value(filepath: str, attribute: str, base_class_name: str):
    """
    Return the value of a class attribute without importing it.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filepath)

    result = {}

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if any(
                isinstance(base, ast.Name) and base.id == base_class_name
                for base in node.bases
            ):
                class_name = node.name
                attr_value = None
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if (
                                isinstance(target, ast.Name)
                                and target.id == attribute
                                and isinstance(stmt.value, ast.Constant)
                                and isinstance(stmt.value.value, str)
                            ):
                                attr_value = stmt.value.value
                if attr_value:
                    result[class_name] = attr_value
                else:
                    raise ValueError(f'No attribute name found on class {class_name}')
    return result


def import_modules_from_dir(root: str|Path, parent_name: str, ignore_list=None):
    files_to_import = []
    for file in Path(root).rglob('*.py'):
        if file.is_file():
            if file.stem.startswith('_'):
                continue
            if ignore_list:
                if any([fnmatch(file.name, x) for x in ignore_list]):
                    continue
            files_to_import.append(file)
    if files_to_import:
        for file in files_to_import:
            import_path = '.'.join([parent_name, file.stem])
            import_module_by_path(file, import_path)


def iter_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield subclass
        yield from iter_subclasses(subclass)

