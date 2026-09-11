from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE = PROJECT_ROOT / "docs" / "referensi_koperasi.xlsx"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "hasil_pencocokan.xlsx"


def timestamped_output_path(output: Path, now: datetime | None = None) -> Path:
    """Tambahkan timestamp ke nama workbook output dan hindari nama yang sudah ada."""
    moment = now or datetime.now().astimezone()
    timestamp = moment.strftime("%Y%m%d_%H%M%S")
    candidate = output.with_name(f"{output.stem}_{timestamp}{output.suffix}")
    sequence = 2
    while candidate.exists():
        candidate = output.with_name(f"{output.stem}_{timestamp}_{sequence}{output.suffix}")
        sequence += 1
    return candidate


class DuplicatePolicy(StrEnum):
    KEEP = "keep"
    FIRST = "first"
    ERROR = "error"


class MatchConfig(BaseModel):
    source: Path
    reference: Path = DEFAULT_REFERENCE
    output: Path
    sheets: list[str]
    address_column: str = "ALAMAT"
    reference_sheet: str = "Export Laporan"
    threshold: float = Field(default=90.0, ge=0, le=100)
    minimum_margin: float = Field(default=5.0, ge=0, le=100)
    duplicate_policy: DuplicatePolicy = DuplicatePolicy.KEEP
    overwrite: bool = False

    @model_validator(mode="after")
    def validate_paths(self) -> "MatchConfig":
        for label, path in (("source", self.source), ("reference", self.reference)):
            if path.suffix.lower() != ".xlsx":
                raise ValueError(f"{label} harus berupa file .xlsx: {path}")
            if not path.is_file():
                raise ValueError(f"File {label} tidak ditemukan: {path}")
        resolved_output = self.output.resolve()
        if resolved_output in {self.source.resolve(), self.reference.resolve()}:
            raise ValueError("File output tidak boleh sama dengan file input")
        if self.output.exists() and not self.overwrite:
            raise ValueError(f"Output sudah ada: {self.output}. Gunakan --overwrite.")
        return self
