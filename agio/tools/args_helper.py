import shlex
from collections import defaultdict


def parse_args_to_dict_and_list(src_args: str|list|tuple, fix_keys_py_names: bool = True) -> (list, dict):
    if isinstance(src_args, str):
        tokens = list(shlex.split(src_args))
    else:
        tokens = list(src_args)
    args = []
    kwargs = defaultdict(list)
    it = iter(tokens)
    for token in it:
        if token == '--':
            continue
        if token.startswith("-"):
            key = token.lstrip("-")
            try:
                value = next(it)
                if value.startswith("-"):
                    kwargs[key].append(True)
                    it = (x for x in [value] + list(it))
                else:
                    kwargs[key].append(value)
            except StopIteration:
                kwargs[key].append(True)
        else:
            args.append(token)
    final_kwargs = {k: v if len(v) > 1 else v[0] for k, v in kwargs.items()}
    if fix_keys_py_names:
        # replace key-name to key_name
        final_kwargs = {k.replace('-', '_'): v for k, v in final_kwargs.items()}
    return args, final_kwargs


def parse_args_to_dict(src_args: list|tuple|str) -> dict:
    if isinstance(src_args, str):
        tokens = list(shlex.split(src_args))
    else:
        tokens = list(src_args)
    values = []
    args = []
    kwargs = {}
    key = None

    def add_key_value(k, v):
        if not v:
            kwargs[k] = True
        elif len(v) == 1:
            kwargs[k] = v[0]
        else:
            kwargs[k] = v

    def convert(value):
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value
    while tokens:
        token = tokens.pop(0)
        if token.startswith('-'):
            if key:
                add_key_value(key, values)
            key = token.lstrip('-')
            values = []
        else:
            values.append(convert(token))

    if key:
        add_key_value(key, values)
    return kwargs


def dict_to_args(src_dict: dict, fix_py_names: bool = True) -> list:
    args = []
    for key, value in src_dict.items():
        if fix_py_names:
            key = key.replace('_', '-')
        args.extend((f'--{key}', str(value)))
    return args


