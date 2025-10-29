from pathlib import Path

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


def render_markdown_from_file(file_path: str|Path) -> str:
    """
    Converts a markdown file to a HTML text
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    return render_markdown_from_string(file_path.read_text(encoding='utf-8'))


def render_markdown_from_string(text: str) -> str:
    """
    Converts a Markdown text to an HTML text

    # TODO: delete any js using bleach
    safe_html = bleach.clean(
        unsafe_html,
        tags=['a', 'p', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'blockquote'],
        attributes={'a': ['href', 'title']},
        protocols=['http', 'https', 'mailto'],
        strip=True
    )
    """
    import mistune

    class CustomRenderer(mistune.HTMLRenderer):
        def image(self, *args, **kwargs):
            return '*Images not supported*'

    markdown = mistune.create_markdown(renderer=CustomRenderer())
    html = markdown(text)
    return html


def shorten_text(s: str, width: int, placeholder: str = "...", from_end=False) -> str:
    if len(s) <= width:
        return s
    if from_end:
        return placeholder+s[width - len(placeholder):]
    else:
        return s[:width - len(placeholder)] + placeholder
