from collections import Counter
from collections.abc import Callable

from .address_parser import parse_address
from .config import DuplicatePolicy, MatchConfig
from .matcher import Matcher
from .models import MatchResult
from .report_writer import write_report
from .workbook_reader import discover_source_sheets, read_reference, read_sources

ProgressCallback = Callable[[str, int, int], None]


def _notify(callback: ProgressCallback | None, message: str, current: int, total: int) -> None:
    if callback:
        callback(message, current, total)


def run(config: MatchConfig, progress: ProgressCallback | None = None) -> Counter[str]:
    _notify(progress, "Mendeteksi seluruh sheet sumber", 0, 0)
    selected_sheets = config.sheets or discover_source_sheets(config.source, config.address_column)
    _notify(progress, f"Membaca {len(selected_sheets)} sheet sumber", 0, 0)
    sources = read_sources(config.source, selected_sheets, config.address_column)
    _notify(progress, f"Data sumber terbaca: {len(sources):,} baris", 1, 1)

    _notify(progress, "Membaca workbook referensi", 0, 0)
    headers, references, _ = read_reference(config.reference, config.reference_sheet)
    _notify(progress, f"Data referensi terbaca: {len(references):,} baris", 1, 1)
    key_counts = Counter(
        (item.province, item.desa, item.kecamatan, item.kabupaten) for item in references
    )
    duplicate_reference_count = sum(1 for count in key_counts.values() if count > 1)
    matcher = Matcher(references, config.threshold, config.minimum_margin)
    results: list[MatchResult] = []
    seen_reference_rows: set[int] = set()
    total_sources = len(sources)
    for position, source in enumerate(sources, 1):
        source.parsed = parse_address(source.address, source.province)
        result = matcher.match(source)
        if result.is_matched and result.reference and result.reference.row in seen_reference_rows:
            if config.duplicate_policy == DuplicatePolicy.FIRST:
                continue
            if config.duplicate_policy == DuplicatePolicy.ERROR:
                raise ValueError(
                    f"Record referensi baris {result.reference.row} cocok lebih dari sekali"
                )
        if result.is_matched and result.reference:
            seen_reference_rows.add(result.reference.row)
        results.append(result)
        _notify(progress, "Mencocokkan data", position, total_sources)

    _notify(progress, "Menulis workbook laporan", 0, 0)
    write_report(
        config.output,
        headers,
        results,
        config.source,
        config.reference,
        selected_sheets,
        config.threshold,
        config.minimum_margin,
        duplicate_reference_count,
    )
    _notify(progress, "Laporan selesai", 1, 1)
    return Counter(result.status.value for result in results)
