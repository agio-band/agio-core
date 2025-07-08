from agio.core.exceptions import PackageLoadingError


def get_release_repository_plugin(repo_url: str, repository_api: str = None):
    from agio.core import plugin_hub

    if not repo_url:
        raise PackageLoadingError('No repo url provided')
    for plugin in plugin_hub.get_plugins_by_type('release_repository'):
        if repository_api and repository_api == plugin.repository_api:
            return plugin
        if plugin.check_is_valid_url(repo_url):
            return plugin
    raise PackageLoadingError(f'No Release repository plugin found for url: {repo_url}')
