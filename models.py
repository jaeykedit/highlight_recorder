from dataclasses import dataclass

@dataclass
class Highlight:
    raw_start: int
    raw_end: int
    memo: str

    def to_display_string(self):
        return f"{self.raw_start//60:02}:{self.raw_start%60:02}~{self.raw_end//60:02}:{self.raw_end%60:02}, {self.memo}"