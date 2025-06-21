import ast


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
