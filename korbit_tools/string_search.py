import fnmatch
import logging
import re
import json
from typing import Optional

from fuzzywuzzy import fuzz

from korbit_tools.models import LineNumberRange

logger = logging.getLogger(__name__)


def split_and_process_snippet(code_snippet: str) -> list[str]:
    code_snippet_lines = code_snippet.strip().splitlines()
    code_snippet_lines[0] = re.sub(r"(\[|\{)?\.\.\.(\]|\})?$", "", code_snippet_lines[0])
    code_snippet_lines[-1] = re.sub(r"(\[|\{)?\.\.\.(\]|\})?$", "", code_snippet_lines[-1])
    code_snippet_lines = list(map(lambda line: line.strip(), code_snippet_lines))

    return code_snippet_lines


def get_line_idx_in_content(end_line: str, content_lines: list[str], fuzzy_match=False) -> int:
    for idx, content_line in enumerate(content_lines):
        if fuzzy_match and fuzz.ratio(end_line, content_line.strip()) > 90 or end_line in content_line:
            return idx
    return -1


def get_line_number_range(
    start_line_idx: int, content_lines: list[str], end_line: str, fuzzy_match=False
) -> Optional[LineNumberRange]:
    end_line_idx = get_line_idx_in_content(end_line, content_lines[start_line_idx:], fuzzy_match) + start_line_idx
    if start_line_idx > end_line_idx:
        logger.debug(f"Couldn't find end line: {end_line} for start_line: {content_lines[start_line_idx]} in content.")
        return
    return LineNumberRange(start_line_idx + 1, end_line_idx + 1)


def get_line_number_ranges_in_content(
    start_line_contents: str, end_line_contents: str, content: str
) -> list[LineNumberRange]:
    content_lines = content.split("\n")
    line_number_ranges = []

    def scan_content(fuzzy_match):
        idx = 0
        # if the code snippet is a single line function call or class definition in single line,
        # when in the code base it's multiple lines, it will fail.
        while idx < len(content_lines):
            line_number_range = None
            if fuzzy_match:
                if fuzz.ratio(start_line_contents, content_lines[idx].strip()) > 90:
                    line_number_range = get_line_number_range(idx, content_lines, end_line_contents, True)
            else:
                if start_line_contents in content_lines[idx]:
                    line_number_range = get_line_number_range(idx, content_lines, end_line_contents)
            if line_number_range is not None:
                line_number_ranges.append(line_number_range)
                idx = line_number_range.end_number - 1
            idx += 1

    scan_content(fuzzy_match=False)

    if len(line_number_ranges) == 0:
        scan_content(fuzzy_match=True)
        if len(line_number_ranges) > 0:
            logger.info(
                f"Used fuzz.ratio() at 90% to find:{start_line_contents} and end_line:{end_line_contents} in content."
            )

    if len(line_number_ranges) == 0:
        logger.debug(f"Couldn't find start_line:{start_line_contents} and end_line:{end_line_contents} in content.")
    return line_number_ranges


def find_line_number_ranges_of_code_snippet_in_content(code_snippet: str, content: str) -> list[LineNumberRange]:
    code_snippet_lines = split_and_process_snippet(code_snippet)
    line_number_ranges = get_line_number_ranges_in_content(code_snippet_lines[0], code_snippet_lines[-1], content)
    return line_number_ranges


def should_ignore_file(file_path: str, rules: list[str]):
    for rule in rules:
        rule_with_wildcard = f"{rule}*" if rule.endswith("/") else rule
        if fnmatch.fnmatch(file_path, rule_with_wildcard):
            return True
    return False

def extract_json_from_text(output: str) -> str:
    """
    LLM often output json withing a code block:
    > I propose the following feedback:
    > ```json
    > {"foo": 1}
    > ```
    This functions extract from text the JSON content of the code block.
    """
    match = re.search(r"```json*\n(.+?)```", output, re.MULTILINE | re.IGNORECASE | re.DOTALL)
    code_block_content = output
    if match:
        code_block_content = match.group(1)

    json_object = json.loads(code_block_content, strict=False, indent=4)
    return json_object
