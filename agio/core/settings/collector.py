import json
import logging
from pathlib import Path

from agio.core import package_hub
from agio.core.settings.generic_types import SettingsType
from agio.core.utils import pipeline_config_dir

logger = logging.getLogger(__name__)


def _get_settings_dir() -> Path:
    return Path(pipeline_config_dir()) / 'settings'


def _get_settings_file(file_name: str) -> Path:
    return _get_settings_dir().joinpath(file_name).with_suffix('.json')



def read_local_settings_values():
    path_list = [
        _get_settings_file('common_settings')
    ]
    # TODO: add studio overrides
    # TODO: add project overrides
    # read data
    settings_data = {}
    for path in path_list:
        if path.exists():
            with path.open(encoding='utf-8') as f:
                data = json.load(f)
            settings_data.update(data)
    return settings_data


def write_local_settings(settings_dict: dict = None, scope: str = None):
    save_path = _get_settings_file('common_settings')
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with save_path.open('w', encoding='utf-8') as f:
        json.dump(settings_dict, f, ensure_ascii=False, indent=4)
    logger.info(f'Saved settings to {save_path}')
    # todo: apply for scopes: project, company

# layout


def collect_local_settings_layout() -> dict:
    return collect_layout(SettingsType.LOCAL)


def collect_workspace_settings_layout() -> dict:
    return collect_layout(SettingsType.WORKSPACE)


def collect_layout(layout_type: str) -> dict:
    # collect packages
    all_packages = package_hub.get_packages()
    # collect layout data
    all_layouts = {}
    for name, pkg in all_packages.items():
        conf = pkg.get_layout_configs(layout_type)
        if conf:
            all_layouts[name] = conf
    # merge layouts to single layout with prefixes
    merged = merge_prefixed_sections(all_layouts)
    # collect settings classes
    all_settings = {}
    for name, pkg in all_packages.items():
        pkg_settings = pkg.get_settings_class(layout_type)
        if pkg_settings:
            all_settings[name] = pkg_settings
    # collect parameters to single list with prefixes
    parameters = {}
    for pkg_name, pkg_settings in all_settings.items():
        settings_schema = pkg_settings(_init_only=True).__schema__()
        for parm_name, parm in settings_schema.items():
            parameters[f'{pkg_name}.{parm_name}'] = parm
    return {
        'sections': merged,
        'parameters': parameters,
    }


def merge_prefixed_sections(configs_data: dict) -> dict:
    # TODO: check not existing parameters
    result = {}
    section_index = {}
    pending_parents = []

    def process_section(_section: dict, pkg_name: str) -> dict:
        _new_section = {}

        for key, value in _section.items():
            if key == "content":
                new_content = []
                for item in value:
                    if isinstance(item, str):
                        new_content.append({
                            "type": "Parameter",
                            "name": f"{pkg_name}.{item}"
                        })
                    elif isinstance(item, dict) and "name" in item:
                        item = item.copy()
                        item["name"] = f"{pkg_name}.{item['name']}"
                        new_content.append(item)
                    else:
                        new_content.append(item)
                _new_section["content"] = new_content
            elif key != "children":
                _new_section[key] = value

        if "children" in _section:
            new_children = {}
            for _child_name, _child_section in _section["children"].items():
                prefixed_child_name = f"{pkg_name}.{_child_name}"
                child_processed = process_section(_child_section, pkg_name)
                new_children[prefixed_child_name] = child_processed
                section_index[prefixed_child_name] = child_processed
            _new_section["children"] = new_children

        return _new_section

    # collect all sections
    for filename, filedata in configs_data.items():
        for section_name, section in filedata.get("sections", {}).items():
            prefixed_name = f"{filename}.{section_name}"
            new_section = process_section(section, filename)
            section_index[prefixed_name] = new_section

            if "parent" in section:
                # to pending
                pending_parents.append((prefixed_name, section["parent"]))
            else:
                # top level section
                result[prefixed_name] = new_section

    # apply parents
    for child_name, parent_name in pending_parents:
        child_section = section_index[child_name]
        if parent_name not in section_index:
            raise ValueError(f"Parent section '{parent_name}' not found for '{child_name}'")

        parent_section = section_index[parent_name]
        child_section.pop('parent', None)
        parent_section.setdefault("children", {})[child_name] = child_section

    return result
