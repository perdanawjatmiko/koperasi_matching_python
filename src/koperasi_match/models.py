from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MatchStatus(StrEnum):
    MATCHED_EXACT = "MATCHED_EXACT"
    MATCHED_UNIQUE_DESA_KECAMATAN = "MATCHED_UNIQUE_DESA_KECAMATAN"
    MATCHED_ALIAS = "MATCHED_ALIAS"
    MATCHED_FUZZY = "MATCHED_FUZZY"
    REVIEW_AMBIGUOUS = "REVIEW_AMBIGUOUS"
    REVIEW_LOW_SCORE = "REVIEW_LOW_SCORE"
    NOT_FOUND = "NOT_FOUND"
    PARSE_FAILED = "PARSE_FAILED"


@dataclass(slots=True)
class ParsedAddress:
    original: str
    desa: str = ""
    kecamatan: str = ""
    kabupaten: str = ""
    province: str = ""
    desa_aliases: tuple[str, ...] = ()
    kecamatan_aliases: tuple[str, ...] = ()
    kabupaten_aliases: tuple[str, ...] = ()
    error: str = ""


@dataclass(slots=True)
class SourceRecord:
    sheet: str
    row: int
    address: str
    province: str
    parsed: ParsedAddress | None = None


@dataclass(slots=True)
class ReferenceRecord:
    row: int
    values: tuple[Any, ...]
    nik: str
    desa_original: str
    kecamatan_original: str
    kabupaten_original: str
    province_original: str
    desa: str
    kecamatan: str
    kabupaten: str
    province: str


@dataclass(slots=True)
class Candidate:
    reference: ReferenceRecord
    score: float


@dataclass(slots=True)
class MatchResult:
    source: SourceRecord
    status: MatchStatus
    reference: ReferenceRecord | None = None
    score: float = 0.0
    second_score: float = 0.0
    margin: float = 0.0
    candidates_checked: int = 0
    note: str = ""
    top_candidates: list[Candidate] = field(default_factory=list)

    @property
    def is_matched(self) -> bool:
        return self.status.value.startswith("MATCHED_")
