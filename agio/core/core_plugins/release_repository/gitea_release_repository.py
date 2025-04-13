import logging
from agio.core.core_plugins.release_repository.github_release_repository import GitHubRepository

logger = logging.getLogger(__name__)


class GiteaRepository(GitHubRepository):
    name = 'gitea'
    check_url_pattern=  None

    def get_api_base_url(self, repository_url: str):
        repo_details = self.parse_url(repository_url)
        return "{schema}://{domain}/api/v1".format(**repo_details)