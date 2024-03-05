import re
from dataclasses import dataclass

from github.File import File

from korbit_tools.models import LineNumberRange
from korbit_tools.string_search import find_line_number_ranges_of_code_snippet_in_content


@dataclass(slots=True, frozen=True, eq=True)
class DiffRepresentation:
    """
    This class is used to represent a diff, and it contains
    methods for extracting and manipulating edited line number ranges within the diff.
    The methods handle single line edits, multiple line edits,
    and extracting modified line number ranges using hunk headers.
    """

    diff: str
    file_path: str
    previous_file_path: str
    # Matches the diff hunk header which provides context for the diff
    regex_diff_hunk_header = r"@@ -\d+,\d+ \+\d+,\d+ @@ (.+)"
    # Matches the entire diff line number group, including the @@ symbols
    regex_diff_line_number_group = r"(@@ -\d+,?\d* \+\d+,?\d* @@)"
    # Matches and captures individual line numbers in the diff
    regex_diff_line_number_pattern = r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@"
    # Matches and captures individual line numbers in the diff when only one line is involved
    regex_diff_one_line_number_pattern = r"@@ -(\d+),?\d* \+(\d+) @@"

    @classmethod
    def from_github_file(cls, github_file: File):
        previous_file_name = github_file.previous_filename or github_file.filename
        return cls(github_file.patch, github_file.filename, previous_file_name)

    @staticmethod
    def _get_line_number_range_from_match_pair(start_line: int, num_edit_lines: int):
        return LineNumberRange(start_number=start_line, end_number=start_line + num_edit_lines)

    def _get_line_numbers_edited_one_line(self, regex_results):
        edited_ranges = [
            (
                self._get_line_number_range_from_match_pair(start_line=int(match[0]), num_edit_lines=1),
                self._get_line_number_range_from_match_pair(start_line=int(match[1]), num_edit_lines=1),
            )
            for match in regex_results
        ]
        return edited_ranges

    def _get_line_numbers_edited_multiple_lines(self, regex_results):
        edited_ranges = []
        for match in regex_results:
            old_diff_context_range = self._get_line_number_range_from_match_pair(
                start_line=int(match[0]), num_edit_lines=int(match[1])
            )
            new_diff_context_range = self._get_line_number_range_from_match_pair(
                start_line=int(match[2]), num_edit_lines=int(match[3])
            )
            edited_ranges.append((old_diff_context_range, new_diff_context_range))

        return edited_ranges

    def _get_line_numbers_edited_in_both_files(self) -> list[tuple[LineNumberRange, LineNumberRange]]:
        if not self.diff:
            return []
        regex_results = re.findall(self.regex_diff_line_number_pattern, self.diff)

        if not regex_results:
            regex_results = re.findall(self.regex_diff_one_line_number_pattern, self.diff)
            return self._get_line_numbers_edited_one_line(regex_results)
        return self._get_line_numbers_edited_multiple_lines(regex_results)

    def get_line_numbers_edited_in_old_file(self) -> list[LineNumberRange]:
        both_edited_line_numbers = self._get_line_numbers_edited_in_both_files()
        old_edited_line_numbers = [el[0] for el in both_edited_line_numbers]

        return old_edited_line_numbers

    def get_line_numbers_edited_in_new_file(self) -> list[LineNumberRange]:
        both_edited_line_numbers = self._get_line_numbers_edited_in_both_files()
        new_edited_line_numbers = [el[1] for el in both_edited_line_numbers]

        return new_edited_line_numbers

    def get_extended_diff_line_ranges_by_hunk_header(self, file_content: str) -> list[LineNumberRange]:
        """
        Extracts modified line number ranges from a diff using hunk headers.
        It expands the range to include the entire function or class where the modifications occurred.
        It returns the modified line number ranges and the corresponding top-level function or class ranges.
        In the following example it will find the line range in the file where the function `a_cool_function` was defined and.
        .. code-block::
        diff --git a/path/to/file.py b/path/to/file.py
        index fa9a0bac7..a8494dae8 100644
        --- a/path/to/file.py
        +++ b/path/to/file.py
        @@ -37,7 +37,7 @@ def a_cool_function() -> None:
                    foofoofoo=None,
                    foofoo=None,
                    barbar=barbar,
        -            something=None,
        +            something=100,
                    fooo=None,
                    foo="",
                    bar=bar,
        """

        if not self.diff:
            return []
        newly_edited_lines = self.get_line_numbers_edited_in_new_file()

        regex_results = re.findall(self.regex_diff_line_number_group, self.diff)
        diff_line_ranges_with_increase_windows = []
        for match, line_number_range in zip(regex_results, newly_edited_lines):
            for diff_line in self.diff.split("\n"):
                hunk_header_result = re.findall(self.regex_diff_hunk_header, diff_line)
                if diff_line.startswith(match) and hunk_header_result:
                    line_range_from_hunk_header = find_line_number_ranges_of_code_snippet_in_content(
                        hunk_header_result[0], file_content
                    )
                    if line_range_from_hunk_header:
                        line_number_range.start_number = line_range_from_hunk_header[0].start_number
            diff_line_ranges_with_increase_windows.append(line_number_range)
        return diff_line_ranges_with_increase_windows
