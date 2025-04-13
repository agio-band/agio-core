from agio.core.plugins.base.base_plugin_release_repository import ReleaseRepositoryPlugin


class GitLabRepository(ReleaseRepositoryPlugin):
    name = 'gitlab'
    check_url_pattern = r'https://gitlab\.com.*'
