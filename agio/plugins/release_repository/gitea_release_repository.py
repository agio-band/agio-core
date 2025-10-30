import logging
from agio.plugins.release_repository.github_release_repository import GitHubRepositoryPlugin

logger = logging.getLogger(__name__)


class GiteaRepositoryPlugin(GitHubRepositoryPlugin):
    name = 'gitea_release_repository'
    repository_api = 'gitea'
    check_url_pattern = None
    check_release_url_key = 'url'

    def get_api_base_url(self, repository_url: str):
        repo_details = self.parse_url(repository_url)
        return "{schema}://{domain}/api/v1".format(**repo_details)
