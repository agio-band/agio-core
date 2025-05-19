from unidecode import unidecode
import re


def pretty_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    units = ['KB', 'MB', 'GB', 'TB', 'PB']
    size = size_bytes / 1024
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} EB"


def slugify(name, placeholder='_'):
    """
    "Some File #Name 123" -> "some_file_name_123"
    """
    return re.sub(r"[^a-zA-Z0-9]+", placeholder,
                  re.sub(r"[^\x00-\x7F]+", placeholder,
                         re.sub(r"[\s\-]+", placeholder, unidecode(name)).lower()))


def unslugify(value: str) -> str:
    return value.replace('-', ' ').replace('_', ' ').title()


def camel_case_to_snake_case(name: str) -> str:
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_case_to_camel_case(name: str, titled_first_letter: bool = True) -> str:
    parts = name.split('_')
    if titled_first_letter:
        parts[0] = parts[0].title()
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])



