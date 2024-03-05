from dataclasses import dataclass


@dataclass(slots=True)
class LineNumberRange:
    start_number: int
    end_number: int
