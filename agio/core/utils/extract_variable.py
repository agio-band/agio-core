
from typing import Any


def get_nested_value(names: list|str, data: Any) -> Any:
    """
    Recursive extract nested value from any object using names or indexes list

    Args:
        names: list of names or string with names separated by dots.
        data: source dict with variables
    """
    if not names:
        return data
    if isinstance(names, str):
        names = names.split('.')
    current_name = names[0]
    remaining_names = names[1:]
    try:
        if isinstance(current_name, str) and current_name.isdigit():
            current_name = int(current_name)
        elif isinstance(current_name, float):
            current_name = int(current_name)
    except ValueError:
        pass # keep original value
    if isinstance(data, set):
        raise TypeError('Set type is not supported')
    if isinstance(data, (list, tuple)):
        if isinstance(current_name, int):
            if 0 <= current_name < len(data):
                return get_nested_value(remaining_names, data[current_name])
            else:
                raise IndexError(f"Index {current_name} out of range: {data}")
        else:
            raise TypeError(
                f"Expected number index, but received '{current_name}' ({type(current_name)})")
    elif isinstance(data, dict):
        if current_name in data:
            return get_nested_value(remaining_names, data[current_name])
        else:
            raise KeyError(f"Key '{current_name}' not found: {data.keys()}")
    else:
        if hasattr(data, current_name):
            return get_nested_value(remaining_names, getattr(data, current_name))
        else:
            raise AttributeError(f"Attribute '{current_name}' not found for {data!r}")


def get_nested_value_or_default(names: list|str, data: dict, default_value=None):
    """
    Try to extract nested value from any object using names or indexes list
    and return default value if value is not found
    """
    try:
        return get_nested_value(names, data)
    except (KeyError, AttributeError, IndexError, TypeError):
        return default_value
