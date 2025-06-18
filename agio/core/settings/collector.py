import json
from pathlib import Path

from agio.core.main import package_hub
from agio.core.settings import LocalSettingsHub, WorkspaceSettingsHub


settings_root = Path('~/.agio/settings').expanduser()


def collect_local_settings() -> LocalSettingsHub:
    # read local settings from files
    settings = read_local_settings_values()
    # create local settings instance with applied values
    return LocalSettingsHub(settings)


def collect_workspace_settings() -> WorkspaceSettingsHub|None:
    from agio.core.workspace.workspace import AWorkspace
    # create workspace instance
    ws = AWorkspace.current()
    if not ws:
        return
    # get workspace settings from server
    settings = {}
    # create workspace settings instance with applied values
    return WorkspaceSettingsHub(settings)


def read_local_settings_values():
    path_list = [
        settings_root/'common_settings.json'
    ]
    # TODO: add project overrides
    # TODO: add studio overrides
    # read data
    settings_data = {}
    for path in path_list:
        if path.exists():
            with path.open(encoding='utf-8') as f:
                data = json.load(f)
            settings_data.update(data)
    return settings_data


def write_local_settings(common_settings: dict = None, projects_settings: dict = None, company_settings: dict = None):
    if company_settings:
        save_path = settings_root / 'common_settings.json'
        with save_path.open('w', encoding='utf-8') as f:
            json.dump(common_settings, f, ensure_ascii=False, indent=4)
    # todo:
    if projects_settings:
        pass
    if company_settings:
        pass

# layout
def pp(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))

def collect_local_settings_layout() -> dict:
    # collect packages
    all_packages = package_hub.get_packages()
    # collect layout data
    all_layouts = {}
    for name, pkg in all_packages.items():
        conf = pkg.get_local_layout_config()
        if conf:
            all_layouts[name] = conf
    pp(all_layouts)
    merged = merge_section_configs(all_layouts)
    # collect settings classes
    all_settings = {}
    for name, pkg in all_packages.items():
        pkg_settings = pkg.get_local_settings_class()
        if pkg_settings:
            all_settings[name] = pkg_settings
    # collect sections to one hierarchy
    parameters = {}
    for pkg_name, pkg_settings in all_settings.items():
        settings_schema = pkg_settings(_init_only=True).__schema__()
        for parm_name, parm in settings_schema.items():
            parameters[f'{pkg_name}.{parm_name}'] = parm

    # pp(merged)
    # print(json.dumps(parameters, indent=2))

    # merge all layouts to one layout description

    # assign parameters to layout
    # return layouts

def collect_workspace_settings_layout() -> dict:
    pass


def merge_section_configs(config_data):
    """
    Объединяет несколько конфигураций секций в единую иерархическую структуру.

    Args:
        config_data (dict): Словарь, где ключи - это имена файлов,
                            а значения - прочитанные YAML-конфигурации
                            в виде словарей.

    Returns:
        OrderedDict: Упорядоченный словарь, представляющий объединенную иерархию секций.
                     Ключи - имена секций, значения - словари с их свойствами
                     (label, order) и вложенными children.
    """

    all_sections = {}
    # Сначала собираем все секции из всех файлов
    for file_name, config in config_data.items():
        if 'sections' in config:
            sections_data = config['sections']
            if isinstance(sections_data, list):
                # Если sections это список, значит, это корневые секции
                for item in sections_data:
                    for section_name, section_props in item.items():
                        all_sections[section_name] = section_props
            elif isinstance(sections_data, dict):
                # Если sections это словарь, значит, это корневые секции
                # или секции с вложенными структурами
                for section_name, section_props in sections_data.items():
                    all_sections[section_name] = section_props

    # Отделяем секции, у которых есть 'parent'
    sections_with_parent = {}
    for section_name, section_props in list(all_sections.items()):
        if 'parent' in section_props:
            sections_with_parent[section_name] = all_sections.pop(section_name)

    # Строим иерархию
    def build_children(parent_section_name=None, sections_pool=None):
        if sections_pool is None:
            sections_pool = all_sections

        children = {}
        for section_name, section_props in sections_pool.items():
            if section_props.get('parent') == parent_section_name:
                # Если секция имеет текущий родитель, добавляем ее
                # и рекурсивно строим ее детей
                section_copy = section_props.copy()
                del section_copy['parent']  # Удаляем parent, так как он уже обработан

                # Находим детей этой секции из оставшихся sections_with_parent
                nested_children = build_children(section_name, sections_with_parent)
                if nested_children:
                    section_copy['children'] = nested_children

                children[section_name] = section_copy

        return children

    # Добавляем все оставшиеся корневые секции (те, у кого нет 'parent' или 'parent' не найден)
    # и их вложенные структуры
    final_hierarchy = {}

    # Сначала добавляем секции, которые изначально были без parent в своих файлах
    for section_name, section_props in all_sections.items():
        if 'parent' not in section_props:
            section_copy = section_props.copy()
            # Ищем их детей среди оставшихся sections_with_parent
            nested_children = build_children(section_name, sections_with_parent)
            if nested_children:
                section_copy['children'] = nested_children
            final_hierarchy[section_name] = section_copy

    # Затем добавляем секции, которые были присоединены через 'parent'
    # и теперь являются частью какой-то ветки
    # Этот шаг по сути уже выполнен в build_children,
    # но важно убедиться, что все секции из sections_with_parent
    # были присоединены. Если какие-то остались, значит, их родитель не был найден.
    # В рамках этой задачи мы предполагаем, что все родители существуют.

    # Сортируем секции по 'order' если он есть, 'last' секции идут в конце
    def sort_sections(sections_dict):
        if not sections_dict:
            return {}

        # Разделяем секции на обычные и "last"
        regular_sections = {}
        last_sections = {}

        for name, props in sections_dict.items():
            if props.get('order') == 'last':
                last_sections[name] = props
            else:
                regular_sections[name] = props

            if 'children' in props:
                props['children'] = sort_sections(props['children'])  # Рекурсивно сортируем детей

        # Объединяем, сначала обычные, потом "last"
        sorted_result = {}
        sorted_result.update(regular_sections)
        sorted_result.update(last_sections)
        return sorted_result

    return sort_sections(final_hierarchy)
