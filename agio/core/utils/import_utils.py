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



