import re
import subprocess
import shlex
import logging
from . import process_tools

logger = logging.getLogger(__name__)


def get_current_branch(repository_root: str):
    cmd = 'git rev-parse --abbrev-ref HEAD'
    branch = process_tools.start_process(shlex.split(cmd), workdir=repository_root, get_output=True)
    return branch.strip()


def has_uncommited_changes(repository_root: str):
    cmd = 'git status --porcelain'
    output = process_tools.start_process(shlex.split(cmd), workdir=repository_root, get_output=True)
    return bool(output.strip())


def has_unpushed_commits(repository_root: str):
    cmd = 'git rev-list "$(git rev-parse --abbrev-ref HEAD)" --not --remotes | wc -l'
    output = subprocess.check_output(cmd, cwd=repository_root, shell=True)
    return output.decode().strip() != '0'


def get_tags(repository_root: str, remote_name: str = 'origin'):
    cmd = 'git tag --list'
    output = process_tools.start_process(shlex.split(cmd), workdir=repository_root, get_output=True)
    local_tags = set(output.split('\n') if output else [])

    cmd = f'git ls-remote --tags {remote_name}'
    try:
        output = process_tools.start_process(shlex.split(cmd), workdir=repository_root, get_output=True)
    except Exception as e:
        logger.warning(str(e))
    remote_tags = set(re.findall(r'refs/tags/([\w.]+)', output))

    return local_tags.union(remote_tags)
