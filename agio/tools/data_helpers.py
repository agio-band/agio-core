from collections import defaultdict


def _deep_tree():
    return defaultdict(deep_tree)


def deep_tree(source: dict = None):
    tree = _deep_tree()
    if not isinstance(source, dict):
        return tree
    for key, value in source.items():
        if isinstance(value, dict):
            tree[key] = deep_tree(value)
        else:
            tree[key] = value
    return tree
