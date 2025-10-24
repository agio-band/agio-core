import re
import subprocess
import shlex
import logging
from . import process_utils

logger = logging.getLogger(__name__)


def get_current_branch(repository_root: str):
    cmd = 'git rev-parse --abbrev-ref HEAD'
    branch = process_utils.start_process(shlex.split(cmd), workdir=repository_root, get_output=True)
    return branch.strip()


def has_uncommited_changes(repository_root: str):
    cmd = 'git status --porcelain --untracked-files=no'
    output = process_utils.start_process(shlex.split(cmd), workdir=repository_root, get_output=True)
    return bool(output.strip())


def has_unpushed_commits(repository_root: str):
    cmd = 'git rev-list "$(git rev-parse --abbrev-ref HEAD)" --not --remotes | wc -l'
    output = subprocess.check_output(cmd, cwd=repository_root, shell=True)
    return output.decode().strip() != '0'


def get_tags(repository_root: str, remote_url: str):
    cmd = 'git tag --list'
    output = process_utils.start_process(shlex.split(cmd), workdir=repository_root, get_output=True)
    local_tags = set(output.strip().split('\n') if output else [])
    cmd = f'git ls-remote --tags {remote_url}'
    try:
        output = process_utils.start_process(shlex.split(cmd), workdir=repository_root, get_output=True)
    except Exception as e:
        logger.warning(str(e))
        raise
    remote_tags = set(re.findall(r'refs/tags/([\w.]+)', output))
    return local_tags, remote_tags


def create_tag(repository_root: str, tag_name: str, message: str = None, push: bool = True):
    """
    Configured ssh required
    """
    repository_root = str(repository_root)
    local_tags, remote_tags = get_tags(repository_root, get_remote_url(repository_root))
    if tag_name in local_tags:
        cmd = f'git tag -d {tag_name}'
        subprocess.call(shlex.split(cmd), cwd=repository_root)
    if push and tag_name in remote_tags:
        cmd = f'git push --delete origin {tag_name}'
        subprocess.call(shlex.split(cmd), cwd=repository_root)
    cmd = f'git tag {tag_name}'
    if message:
        cmd += f' -m "{message}"'
    subprocess.call(shlex.split(cmd), cwd=repository_root)
    if push:
        cmd = f'git push origin {tag_name}'
        subprocess.call(shlex.split(cmd), cwd=repository_root)


def delete_tag(repository_root: str, tag_name: str, push: bool = True):
    cmd = f'git tag -d {tag_name}'
    subprocess.call(shlex.split(cmd), cwd=repository_root)
    if push:
        cmd = f'git push origin {tag_name}'
        subprocess.call(shlex.split(cmd), cwd=repository_root)


def get_remote_url(repository_root: str, remote: str = 'origin'):
    cmd = 'git remote get-url ' + remote
    return process_utils.start_process(shlex.split(cmd), workdir=repository_root, get_output=True).strip() or None
