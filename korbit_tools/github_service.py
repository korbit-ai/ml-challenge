import fnmatch
import logging
import os
import uuid
import zipfile
from io import BytesIO
from typing import Iterator, Optional

import github
import requests
from github.PullRequest import PullRequest
from github.Repository import Repository

from korbit_tools.diff_representation import DiffRepresentation
from korbit_tools.local_file import LocalFile, from_content_file
from korbit_tools.llm_utils import count_token_string

logger = logging.getLogger(__name__)

# We limit the number of token per file to be < 50k tokens otherwise we can't do the review
CONTENT_FILE_TOKEN_LIMIT = 50000


class GithubUtils:

    @staticmethod
    def get_pull_request_files(
        pull_request: PullRequest, ignore_rules: Optional[list[str]] = None
    ) -> list[DiffRepresentation]:
        if not ignore_rules:
            ignore_rules = GithubUtils.get_ignore_file_rules()
        return [
            DiffRepresentation.from_github_file(file)
            for file in pull_request.get_files()
            if not GithubUtils.should_ignore_file(file.filename, ignore_rules)
            and file.status != "removed"
        ]

    @staticmethod
    def get_pull_request_content_files(
        repository: Repository, pull_request: PullRequest, file: DiffRepresentation
    ) -> LocalFile | None:
        content_file = GithubUtils.get_repository_content_from_path(
            repository, file.file_path, pull_request.head.sha
        )
        if content_file:
            return content_file[0]
        return None

    @staticmethod
    def get_pull_request_content_file_iter(
        repository: Repository,
        pull_request: PullRequest,
        allowed_extensions: Optional[list[str]] = None,
    ) -> Iterator[tuple[LocalFile, DiffRepresentation]]:
        """
        Returns an iterator of tuples containing LocalFile and
        DiffRepresentation for the content files in a pull request.

        Args:
            repository: repository containing the pull request.
            pull_request: The pull request for which the content are being retrieved.
            allowed_extensions: A list of extensions that will be accepted.

        Yields:
            Iterator[tuple[LocalFile, DiffRepresentation]]: A tuple containing
            the content file and its corresponding pull request file.

        """
        pr_files = GithubUtils.get_pull_request_files(pull_request)
        for pr_file in pr_files:
            if not any(pr_file.file_path.endswith(extension) for extension in allowed_extensions):
                continue
            content_file = GithubUtils.get_pull_request_content_files(
                repository, pull_request, pr_file
            )
            if content_file:
                yield content_file, pr_file
            else:
                logger.debug("Skipping file: " + pr_file.file_path)

    @staticmethod
    def get_repository_content_from_path(
        repository: Repository, path: str, ref: str
    ) -> list[LocalFile]:
        """
        Get repository content from the specified path and reference.

        Args:
            repository (Repository): The repository object.
            path (str): The path to the content folder or file.
            ref (str): The reference to the content.

        Returns:
            list[LocalFile]: A list of LocalFile objects representing the content.
        """

        try:
            contents = repository.get_contents(path, ref)
        except github.GithubException:
            return []

        if isinstance(contents, list):
            local_files = []
            for content_file in contents:
                try:
                    local_files.append(from_content_file(content_file))
                except UnicodeDecodeError as e:
                    logger.debug(f"Couldn't decode file {path}: {str(e)}")
                    continue

        else:
            try:
                local_files = [from_content_file(contents)]
            except UnicodeDecodeError as e:
                logger.debug(f"Couldn't decode file {path}: {str(e)}")
                local_files = []

        return local_files

    @staticmethod
    def get_ignore_file_rules() -> list[str]:
        default_korbitignore_path = ".korbitignore"
        with open(default_korbitignore_path, "r") as file:
            default_korbitignore_lines = file.readlines()
        korbit_ignore_lines = default_korbitignore_lines
        return [line.strip() for line in korbit_ignore_lines]

    @staticmethod
    def should_ignore_file(file_path: str, rules: list[str]):
        for rule in rules:
            rule_with_wildcard = f"{rule}*" if rule.endswith("/") else rule
            if fnmatch.fnmatch(file_path, rule_with_wildcard):
                return True
        return False


def extract_zip_content_to_folder(
    content: bytes, base_path: str, parent_dir=None
) -> tuple[str, str]:
    """
    Extracts the content of a zip file to a specified folder.

    Args:
        content (bytes): The content of the zip file.
        base_path (str): The base path where the content will be extracted.
        parent_dir (str, optional): The parent directory within the zip file to be extracted. Defaults to None.

    Returns:
        tuple[str, str]: A tuple containing the write path and the full path of the extracted content.
    """
    try:
        zip_file = zipfile.ZipFile(BytesIO(content))
    except zipfile.BadZipFile:
        print(
            f"Received bytes that are not a valid zip file, might be an empty repo being scanned."
            f" Length of bytes received: {len(content)}"
        )
    temp_dir_name = str(uuid.uuid4())
    write_path = os.path.join(base_path, temp_dir_name)
    if parent_dir:
        repo_dir_path = parent_dir
        _write_path = os.path.join(write_path, parent_dir)
        zip_file.extractall(_write_path)
    else:
        zip_info = zip_file.infolist()[0]
        repo_dir_path = zip_info.filename
        zip_file.extractall(write_path)
    full_path = os.path.join(write_path, repo_dir_path)
    return write_path, full_path


def download_repository(repository: Repository, ref: str, folder_path=".") -> str:
    """
    Download a repository and return the extracted content.

    Args:
        repository: The repository object to download from.
        ref: The reference to download from.
        folder_path: The path of the download folder.

    Returns:
        A the local path to the downloaded repository.
    """
    archive_link = repository.get_archive_link("zipball", ref)
    response = requests.get(archive_link, stream=True)
    _, full_path = extract_zip_content_to_folder(response.content, folder_path)
    return full_path
