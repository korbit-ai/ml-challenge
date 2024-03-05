import logging
import os
from dataclasses import dataclass
from typing import Optional

from github.ContentFile import ContentFile

from korbit_tools import language_extensions
from korbit_tools.models import LineNumberRange

logger = logging.getLogger(__name__)


@dataclass
class LocalFile:
    contents: str
    filename: str
    path: str
    html_url: str
    full_local_path: str = ""

    def get_truncated_contents(self, max_char_limit):
        return self.contents[:max_char_limit]

    def get_programming_language(self) -> str:
        language = ""

        try:
            extension = os.path.splitext(self.html_url)[1].strip(".")
            language = language_extensions.mapping.get(extension, "")

        except OSError as e:
            logger.error(f"Was unable to extract the extension from the file URL: {e}")

        return language

    def get_number_of_lines(self) -> int:
        return get_number_of_lines(self.contents)

    def should_process_file(self, file_extensions=[".py", ".js", ".jsx", ".ts", ".tsx"]) -> bool:
        return any(self.filename.lower().endswith(extension) for extension in file_extensions)

    def allow_llm_run(self):
        """Check if the function should process the file and if the contents are not empty."""
        return self.should_process_file() and len(self.contents.strip()) > 0


def get_content_between_line_numbers(line_number_range: LineNumberRange, content: str) -> str:
    lines = content.split("\n")
    start_idx = line_number_range.start_number - 1
    return "\n".join(lines[start_idx : line_number_range.end_number])


def get_number_of_lines(content: str) -> int:
    return len(content.split("\n"))


def from_content_file(content_file: ContentFile) -> LocalFile:
    return LocalFile(
        contents=content_file.decoded_content.decode(),
        filename=content_file.name,
        path=content_file.path,
        html_url=content_file.html_url,
    )


def from_content_file_safely(content_file: ContentFile) -> Optional[LocalFile]:
    try:
        return LocalFile(
            contents=content_file.decoded_content.decode(),
            filename=content_file.name,
            path=content_file.path,
            html_url=content_file.html_url,
        )
    except UnicodeDecodeError:
        logger.warn(f"Couldn't decode file {content_file.path}")
    except AssertionError:
        # When ContentFile is > 1MB we can't decode it
        # https://github.blog/changelog/2022-05-03-increased-file-size-limit-when-retrieving-file-contents-via-rest-api/
        if content_file.encoding == "none":
            logger.debug(f"Couldn't decode file {content_file.path} due to large size ({content_file.size} byte)")
    return None
