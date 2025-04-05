def get_release_repository_plugin(repo_url: str, vendor_name: str = None):
    from agio.core.init_core import plugin_hub

    for plugin in plugin_hub.get_plugins_by_type('release_repository'):
        if vendor_name and vendor_name == plugin.name:
            return plugin
        if plugin.check_is_valid_url(repo_url):
            return plugin
    raise ValueError(f'No Release repository plugin found for url: {repo_url}')

    # vendors_dir = Path(__file__).parent.joinpath('vendors')
    # for vendor in vendors_dir.iterdir():
    #     if vendor.is_file():
    #         module_name = vendor.stem
    #         import_name = f"{__name__}.{module_name}"
    #         releaser = importlib.import_module(import_name)
    #         for obj_name, obj in releaser.__dict__.items():
    #             if inspect.isclass(obj) and issubclass(obj, ReleaseRepositoryPlugin) and obj is not ReleaseRepositoryPlugin:
    #                 if vendor_name and vendor_name == obj.name:
    #                     return obj(repo_url)
    #                 if obj.check_is_valid_url(repo_url):
    #                     return obj(repo_url)
    # raise ValueError(f'No Release helper found for url: {repo_url}')