import json
import logging
from pathlib import Path

from agio.core import package_hub
from agio.core.settings.generic_types import SettingsType
from agio.core.utils import pipeline_config_dir, text_utils
from agio.core.utils.modules_utils import import_object_by_dotted_path
from agio.core.settings.package_settings import APackageSettings


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


def _find_nodes_by_type(obj, type_name: str):
    """
    Iter items by type
    """
    if isinstance(obj, dict):
        if obj.get('type') == type_name:
            yield obj
        for value in obj.values():
            yield from _find_nodes_by_type(value, type_name)
    elif isinstance(obj, list):
        for item in obj:
            yield from _find_nodes_by_type(item, type_name)


def _expand_parameter_class(parm_class):
    new_parm = {
        'type': 'GroupBox',
        'content': []
    }
    class_to_import = parm_class.pop('class', None)
    if not class_to_import:
        raise Exception(f'Class to import not specified')
    cls = import_object_by_dotted_path(class_to_import)
    if not issubclass(cls, APackageSettings):
        raise TypeError(f'Param class {parm_class} must be a subclass of APackageSettings')
    obj = cls(_init_only=1)
    new_parm['label'] = obj.label
    params = obj.__schema__()
    exclude = parm_class.pop('exclude', None)
    if exclude:
        params = {k: v for k, v in params.items() if k not in exclude}
    new_parm['content'] = [{'type': 'Parameter', 'name': par} for par in params.keys()]
    parm_class.update(new_parm)
    return params


def _rextract_markdown(param: dict):
    file_path = param.pop('abs_file', '')
    if not file_path:
        raise Exception(f'Param {param} must have a file path')
    file_path = Path(file_path)
    if not file_path.exists():
        raise Exception(f'File not found: {file_path}')
    text = text_utils.render_markdown_from_file(file_path)
    param['type'] = 'Html'
    param['text'] = text


def _fix_param_names(params: dict, package_name: str):
    for parm in _find_nodes_by_type(params, 'Parameter'):
        parm['name'] = '.'.join([package_name, parm['name']])


def _update_conf(package_name: str, layout: dict) -> tuple[dict, dict]:
    # expand ParameterClass
    new_parameters = {}
    for parm in _find_nodes_by_type(layout, 'ParameterClass'):
        new_parameters = _expand_parameter_class(parm)
    # expand content from files
    for parm in _find_nodes_by_type(layout, 'MarkdownText'):
        _rextract_markdown(parm)
    # apply package name
    _fix_param_names(layout, package_name)
    new_parameters = {f'{package_name}.{k}': v for k, v in new_parameters.items()}
    return layout, new_parameters


def collect_layout(layout_type: str) -> dict:
    # collect packages
    all_packages = package_hub.get_packages()
    # collect layout data
    parameters = {}
    all_layouts = {}
    for name, pkg in all_packages.items():
        conf = pkg.get_layout_configs(layout_type)
        if conf:
            conf, params = _update_conf(name, conf)
            parameters.update(params)
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
