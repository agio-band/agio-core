from agio.core.plugins.base.release_repository_base import ReleaseRepositoryPlugin


class GitLabRepositoryPlugin(ReleaseRepositoryPlugin):
    name = 'gitlab_release_repository'
    repository_api = 'gitlab'
    check_url_pattern = r'https://gitlab\.com.*'
