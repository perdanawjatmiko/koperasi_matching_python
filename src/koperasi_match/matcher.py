from collections import defaultdict
from itertools import product

from rapidfuzz.fuzz import ratio

from .models import Candidate, MatchResult, MatchStatus, ReferenceRecord, SourceRecord


class ReferenceIndex:
    def __init__(self, records: list[ReferenceRecord]) -> None:
        self.records = records
        self.by_province: dict[str, list[ReferenceRecord]] = defaultdict(list)
        self.by_exact: dict[tuple[str, str, str, str], list[ReferenceRecord]] = defaultdict(list)
        self.by_desa_kec: dict[tuple[str, str, str], list[ReferenceRecord]] = defaultdict(list)
        self.by_desa: dict[tuple[str, str], list[ReferenceRecord]] = defaultdict(list)
        for record in records:
            self.by_province[record.province].append(record)
            self.by_exact[
                (record.province, record.desa, record.kecamatan, record.kabupaten)
            ].append(record)
            self.by_desa_kec[(record.province, record.desa, record.kecamatan)].append(record)
            self.by_desa[(record.province, record.desa)].append(record)


class Matcher:
    def __init__(
        self, records: list[ReferenceRecord], threshold: float = 90, minimum_margin: float = 5
    ):
        self.index = ReferenceIndex(records)
        self.threshold = threshold
        self.minimum_margin = minimum_margin

    def match(self, source: SourceRecord) -> MatchResult:
        parsed = source.parsed
        if parsed is None or parsed.error or not parsed.desa:
            return MatchResult(
                source, MatchStatus.PARSE_FAILED, note=parsed.error if parsed else "Belum diparsing"
            )
        if not parsed.kecamatan:
            return self._review_desa_only(source)

        exact = self.index.by_exact.get(
            (parsed.province, parsed.desa, parsed.kecamatan, parsed.kabupaten), []
        )
        if len(exact) == 1:
            return MatchResult(source, MatchStatus.MATCHED_EXACT, exact[0], 100, 0, 100, 1)
        if len(exact) > 1:
            return self._ambiguous(source, exact, "Lebih dari satu exact match")

        desa_kec = self.index.by_desa_kec.get((parsed.province, parsed.desa, parsed.kecamatan), [])
        if len(desa_kec) == 1:
            return MatchResult(
                source,
                MatchStatus.MATCHED_UNIQUE_DESA_KECAMATAN,
                desa_kec[0],
                100,
                0,
                100,
                1,
                "Kabupaten berbeda/kosong; desa dan kecamatan unik",
            )
        if len(desa_kec) > 1:
            return self._ambiguous(source, desa_kec, "Desa dan kecamatan tidak unik")

        alias_hits = []
        for desa, kecamatan, kabupaten in product(
            parsed.desa_aliases or (parsed.desa,),
            parsed.kecamatan_aliases or (parsed.kecamatan,),
            parsed.kabupaten_aliases or (parsed.kabupaten,),
        ):
            alias_hits.extend(
                self.index.by_exact.get((parsed.province, desa, kecamatan, kabupaten), [])
            )
            if not alias_hits:
                alias_hits.extend(
                    self.index.by_desa_kec.get((parsed.province, desa, kecamatan), [])
                )
        alias_hits = list({record.row: record for record in alias_hits}.values())
        if len(alias_hits) == 1:
            return MatchResult(source, MatchStatus.MATCHED_ALIAS, alias_hits[0], 100, 0, 100, 1)
        if len(alias_hits) > 1:
            return self._ambiguous(
                source, alias_hits, "Nama alternatif menghasilkan beberapa kandidat"
            )

        candidates = self._candidate_pool(source)
        scored = sorted(
            (Candidate(record, self._weighted_score(source, record)) for record in candidates),
            key=lambda item: (-item.score, item.reference.row),
        )
        if not scored:
            return MatchResult(
                source,
                MatchStatus.NOT_FOUND,
                candidates_checked=0,
                note="Tidak ada kandidat pada provinsi",
            )
        best = scored[0]
        second_score = scored[1].score if len(scored) > 1 else 0.0
        margin = best.score - second_score
        top = scored[:3]
        if best.score >= self.threshold and margin >= self.minimum_margin:
            return MatchResult(
                source,
                MatchStatus.MATCHED_FUZZY,
                best.reference,
                best.score,
                second_score,
                margin,
                len(scored),
                top_candidates=top,
            )
        status = (
            MatchStatus.REVIEW_AMBIGUOUS
            if best.score >= self.threshold
            else MatchStatus.REVIEW_LOW_SCORE
        )
        note = (
            "Selisih kandidat terbaik terlalu kecil"
            if status == MatchStatus.REVIEW_AMBIGUOUS
            else "Skor di bawah threshold"
        )
        return MatchResult(
            source,
            status,
            score=best.score,
            second_score=second_score,
            margin=margin,
            candidates_checked=len(scored),
            note=note,
            top_candidates=top,
        )

    def _candidate_pool(self, source: SourceRecord) -> list[ReferenceRecord]:
        parsed = source.parsed
        assert parsed is not None
        province = self.index.by_province.get(parsed.province, [])
        if parsed.kabupaten:
            same_kab = [record for record in province if record.kabupaten == parsed.kabupaten]
            if same_kab:
                same_kec = [record for record in same_kab if record.kecamatan == parsed.kecamatan]
                return same_kec or same_kab
        same_kec = [record for record in province if record.kecamatan == parsed.kecamatan]
        return same_kec or province

    def _review_desa_only(self, source: SourceRecord) -> MatchResult:
        parsed = source.parsed
        assert parsed is not None
        exact_records = []
        for desa in parsed.desa_aliases or (parsed.desa,):
            exact_records.extend(self.index.by_desa.get((parsed.province, desa), []))
        exact_records = list({record.row: record for record in exact_records}.values())
        if exact_records:
            top = [Candidate(record, 100.0) for record in exact_records[:3]]
            return MatchResult(
                source,
                MatchStatus.REVIEW_AMBIGUOUS,
                score=100,
                second_score=100 if len(exact_records) > 1 else 0,
                margin=0,
                candidates_checked=len(exact_records),
                note="Alamat hanya memuat desa; kecamatan dan kabupaten perlu dikonfirmasi",
                top_candidates=top,
            )

        province_records = self.index.by_province.get(parsed.province, [])
        scored = sorted(
            (
                Candidate(
                    record,
                    max(
                        ratio(alias, record.desa) for alias in parsed.desa_aliases or (parsed.desa,)
                    ),
                )
                for record in province_records
            ),
            key=lambda item: (-item.score, item.reference.row),
        )
        best_score = scored[0].score if scored else 0
        second_score = scored[1].score if len(scored) > 1 else 0
        return MatchResult(
            source,
            MatchStatus.REVIEW_LOW_SCORE,
            score=best_score,
            second_score=second_score,
            margin=best_score - second_score,
            candidates_checked=len(scored),
            note="Alamat hanya memuat desa; kecamatan dan kabupaten perlu dikonfirmasi",
            top_candidates=scored[:3],
        )

    @staticmethod
    def _weighted_score(source: SourceRecord, reference: ReferenceRecord) -> float:
        parsed = source.parsed
        assert parsed is not None
        desa_score = max(
            ratio(alias, reference.desa) for alias in parsed.desa_aliases or (parsed.desa,)
        )
        kec_score = max(
            ratio(alias, reference.kecamatan)
            for alias in parsed.kecamatan_aliases or (parsed.kecamatan,)
        )
        if parsed.kabupaten:
            kab_score = max(
                ratio(alias, reference.kabupaten)
                for alias in parsed.kabupaten_aliases or (parsed.kabupaten,)
            )
            return round(0.5 * desa_score + 0.3 * kec_score + 0.2 * kab_score, 2)
        return round(0.625 * desa_score + 0.375 * kec_score, 2)

    @staticmethod
    def _ambiguous(source: SourceRecord, records: list[ReferenceRecord], note: str) -> MatchResult:
        top = [Candidate(record, 100.0) for record in records[:3]]
        return MatchResult(
            source,
            MatchStatus.REVIEW_AMBIGUOUS,
            score=100,
            second_score=100,
            margin=0,
            candidates_checked=len(records),
            note=note,
            top_candidates=top,
        )
