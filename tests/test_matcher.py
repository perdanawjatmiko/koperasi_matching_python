from koperasi_match.address_parser import parse_address
from koperasi_match.matcher import Matcher
from koperasi_match.models import MatchStatus, ReferenceRecord, SourceRecord


def ref(row, desa, kec, kab, prov="ACEH"):
    return ReferenceRecord(
        row, (str(row), desa, kec, kab, prov), str(row), desa, kec, kab, prov, desa, kec, kab, prov
    )


def source(address, parsed):
    return SourceRecord("ACEH", 8, address, "ACEH", parsed)


def test_exact_and_unique_match():
    matcher = Matcher([ref(2, "LAYEUN", "LEUPUNG", "ACEH BESAR")])
    exact = source("x", parse_address("LAYEUN, LEUPUNG, ACEH BESAR", "ACEH"))
    assert matcher.match(exact).status == MatchStatus.MATCHED_EXACT
    unique = source("x", parse_address("LAYEUN, LEUPUNG", "ACEH"))
    assert matcher.match(unique).status == MatchStatus.MATCHED_UNIQUE_DESA_KECAMATAN


def test_ambiguous_is_not_auto_matched():
    matcher = Matcher(
        [
            ref(2, "SUKA MAJU", "BANDAR", "ACEH BESAR"),
            ref(3, "SUKA MAJU", "BANDAR", "BENER MERIAH"),
        ]
    )
    item = source("x", parse_address("SUKA MAJU, BANDAR", "ACEH"))
    assert matcher.match(item).status == MatchStatus.REVIEW_AMBIGUOUS


def test_fuzzy_threshold_and_margin():
    matcher = Matcher(
        [
            ref(2, "LAYEUN", "LEUPUNG", "ACEH BESAR"),
            ref(3, "LAM AWE", "PEUKAN BADA", "ACEH BESAR"),
        ],
        threshold=80,
        minimum_margin=5,
    )
    item = source("x", parse_address("LAYEUNN, LEUPUNG, ACEH BESAR", "ACEH"))
    assert matcher.match(item).status == MatchStatus.MATCHED_FUZZY


def test_desa_only_always_requires_review_even_when_unique():
    matcher = Matcher([ref(2, "SIMPANG JAYA", "TEUPAH SELATAN", "SIMEULUE")])
    item = source("SIMPANG JAYA", parse_address("SIMPANG JAYA", "ACEH"))
    result = matcher.match(item)
    assert result.status == MatchStatus.REVIEW_AMBIGUOUS
    assert result.reference is None
    assert result.top_candidates[0].reference.row == 2


def test_desa_kecamatan_without_kabupaten_can_match_unique_reference():
    matcher = Matcher([ref(2, "AIR PINANG", "SIMEULUE TIMUR", "SIMEULUE")])
    item = source(
        "DESA AIR PINANG KEC. SIMEULUE TIMUR",
        parse_address("DESA AIR PINANG KEC. SIMEULUE TIMUR", "ACEH"),
    )
    assert matcher.match(item).status == MatchStatus.MATCHED_UNIQUE_DESA_KECAMATAN


def test_pekon_name_uses_alias_but_preserves_parsed_name():
    matcher = Matcher([ref(2, "PEJAJARAN", "KOTA AGUNG BARAT", "TANGGAMUS", "LAMPUNG")])
    parsed = parse_address("PEKON PEJAJARAN KEC. KOTAAGUNG KAB. TANGGAMUS", "LAMPUNG")
    result = matcher.match(SourceRecord("LAMPUNG", 8, parsed.original, "LAMPUNG", parsed))
    assert parsed.desa == "PEKON PEJAJARAN"
    assert result.status == MatchStatus.MATCHED_FUZZY
