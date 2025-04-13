def get_release_repository_plugin(repo_url: str, plugin_name: str = None):
    from agio.core.init_core import plugin_hub

    if not repo_url:
        raise ValueError('No repo url provided')
    for plugin in plugin_hub.get_plugins_by_type('release_repository'):
        if plugin_name and plugin_name == plugin.name:
            return plugin
        if plugin.check_is_valid_url(repo_url):
            return plugin
    raise ValueError(f'No Release repository plugin found for url: {repo_url}')
