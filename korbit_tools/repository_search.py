from __future__ import annotations

import os
from collections import Counter
from logging import getLogger
from typing import Iterator

from korbit_tools.github_service import GithubUtils
from korbit_tools.local_file import LocalFile
from korbit_tools.string_search import should_ignore_file

KORBIT_IGNORE_NAME = ".korbitignore"


class LocalRepository:
    repo_path: str
    ignore_rules: list[str]
    logger = getLogger(__name__)

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.ignore_rules = GithubUtils.get_ignore_file_rules()

    def read_file(self, full_path) -> LocalFile | None:
        a_file = None
        path = os.path.relpath(full_path, self.repo_path)
        try:
            with open(full_path, "r") as f:
                contents = f.read()
                a_file = LocalFile(
                    contents=contents,
                    filename=os.path.basename(f.name),
                    path=path,
                    html_url="",
                    full_local_path=full_path,
                )
        except FileNotFoundError:
            if KORBIT_IGNORE_NAME not in full_path:
                self.logger.exception(f"Couldn't find file {path} to read.")
            else:
                self.logger.debug(f".korbitignore not found while reading {full_path}.")
        except UnicodeDecodeError as e:
            self.logger.debug(f"Couldn't decode file {path}: {str(e)}")
        return a_file

    def repository_content_iter(self, path="") -> Iterator[LocalFile]:
        """
        Iterates through the content of the repository at the specified path and yields LocalFile objects.

        Args:
            path (str): The path within the repository to iterate through. Defaults to an empty string.

        Yields:
            Iterator[LocalFile]: A local file within the repository.
        """
        full_path = os.path.join(self.repo_path, path)
        if os.path.isfile(full_path):
            list_files = [(self.repo_path, [], [path])]
        else:
            list_files = os.walk(full_path)

        for root, _, files in list_files:
            for file_name in files:
                full_file_path = os.path.join(root, file_name)
                if not should_ignore_file(full_file_path, self.ignore_rules):
                    local_file = self.read_file(full_file_path)
                    if local_file:
                        yield local_file

    def count_languages_extensions(self) -> Counter[str]:
        """Return the extension of all the files in a repo folder"""
        extensions: Counter[str] = Counter()
        for _, _, files in os.walk(self.repo_path):
            for file in files:
                extension = os.path.splitext(file)[1]
                if extension:
                    extensions[extension] += 1
        return extensions

    def get_folder_tree(self, depth: int) -> dict[str, list[str]]:
        """
        Retrieve the folder tree structure up to a specified depth.

        Args:
            depth (int): The maximum depth of the folder tree to retrieve.

        Returns:
            dict[str, list[str]]: A dictionary representing the folder tree structure, with folder names as keys and lists of subfolder and file names as values.
        """
        tree = {}
        for root, dirs, files in os.walk(self.repo_path):
            level = root.count(os.sep) - self.repo_path.count(os.sep)
            if level <= depth:
                name = root.replace(self.repo_path, "/")
                dirs[:] = [d.replace(self.repo_path, "/") for d in dirs]
                files[:] = [f.replace(self.repo_path, "/") for f in files]
                tree[name] = dirs + files
        return tree

    def get_full_file_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.join(self.repo_path, path)
