import re


def render_template(template: str, context: dict) -> str:
    """
    Render string template with context

    Simple variable: "{varname}"
    Optional variable: "<{varname}>"
    Optional variable with prefix: "<v{version}>"
    Optional variable with suffix: "<{version}_>other"
    Formatting: {version:03d}
    """
    pattern = re.compile(r"((<(.*))(\{([\w_<>:-]+)})(.*)>)|({([\w_<>:-]+)})")
    match = pattern.findall(template)
    out_text = template
    if match:
        for m in match:
            is_optional = False
            if m[7]:
                prefix = suffix = ''
                variable = m[7]
                orig = m[6]
            else:
                is_optional = True
                prefix = m[2]
                suffix = m[5]
                variable = m[4]
                orig = m[0]
            if variable.split(':')[0] not in context:
                if is_optional:
                    out_text = out_text.replace(orig, '')
                    continue
                else:
                    raise ValueError(f"Variable [{variable.split(':')[0]}] not found in context")
            var_result = f'{{{variable}}}'.format(**context)
            new_value = f"{prefix}{var_result}{suffix}"
            out_text = out_text.replace(orig, new_value)
    return out_text

