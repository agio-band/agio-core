import ast
import importlib.util
import sys


def import_module_by_path(path: str, name: str = None):
    spec = importlib.util.spec_from_file_location(name or "module", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def import_object_by_dotted_path(dotted_path: str) -> object:
    """
    Import and return object inside module by dotted path.
    Path example: "my_module.my_submodule.MyClass"
    """
    module_name, object_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
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
