from agio.core.plugins.base.remote_repository_base import RemoteRepositoryPlugin


class GitLabRepositoryPlugin(RemoteRepositoryPlugin):
    name = 'gitlab_release_repository'
    repository_api = 'gitlab'
    check_url_pattern = r'https://gitlab\.com.*'
