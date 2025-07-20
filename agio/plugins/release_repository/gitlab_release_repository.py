from agio.core.plugins.base_remote_repository import RemoteRepositoryPlugin


class GitLabRepositoryPlugin(RemoteRepositoryPlugin):
    name = 'gitlab_release_repository'
    repository_api = 'gitlab'
    check_url_pattern = r'https://gitlab\.com.*'
