from agio.core.plugins.base.release_repository_base_plugin import ReleaseRepositoryPlugin


class GitLabRepository(ReleaseRepositoryPlugin):
    name = 'github'
    check_url_pattern = r'https://gitlab\.com.*'
