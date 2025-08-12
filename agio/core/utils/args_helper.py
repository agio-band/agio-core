import shlex

def parse_args_to_dict(src_args: list|str) -> dict:
    if isinstance(src_args, str):
        tokens = list(shlex.split(src_args))
    else:
        tokens = list(src_args)
    result = {}
    key = None
    values = []

    def add_key_value(k, v):
        if not v:
            result[k] = True
        elif len(v) == 1:
            result[k] = v[0]
        else:
            result[k] = v

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

    return result