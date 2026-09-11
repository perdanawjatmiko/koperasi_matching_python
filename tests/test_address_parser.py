import pytest

from koperasi_match.address_parser import parse_address


def test_parse_comma_and_trailing_comma():
    parsed = parse_address("Paya Bakung, Hamparan Perak, Deli Serdang,", "SUMUT")
    assert (parsed.desa, parsed.kecamatan, parsed.kabupaten, parsed.province) == (
        "PAYA BAKUNG",
        "HAMPARAN PERAK",
        "DELI SERDANG",
        "SUMATERA UTARA",
    )


def test_parse_ignores_fourth_and_later_comma_parts():
    parsed = parse_address(
        "LHOK TIMON, SETIA BHAKTI (SETIA BAKTI), ACEH JAYA, ACEH (NAD)",
        "PROVINSI ACEH",
    )
    assert not parsed.error
    assert parsed.desa == "LHOK TIMON"
    assert parsed.kecamatan == "SETIA BHAKTI"
    assert parsed.kecamatan_aliases == ("SETIA BHAKTI", "SETIA BAKTI")
    assert parsed.kabupaten == "ACEH JAYA"
    assert parsed.province == "ACEH"


def test_parse_labels():
    parsed = parse_address("DESA SAWO KEC. SAWO KAB. NIAS UTARA", "SUMUT")
    assert (parsed.desa, parsed.kecamatan, parsed.kabupaten) == ("SAWO", "SAWO", "NIAS UTARA")


@pytest.mark.parametrize(
    "desa_label", ["DES", "DES,", "DES.", "DS", "DS.", "DESA", "KEL.", "Kelurahan"]
)
@pytest.mark.parametrize("kecamatan_label", ["KEC", "KEC,", "KEC."])
@pytest.mark.parametrize("kabupaten_label", ["KAB", "KAB,", "KAB."])
def test_parse_administrative_label_variants(desa_label, kecamatan_label, kabupaten_label):
    parsed = parse_address(
        f"{desa_label} LHOK TIMON {kecamatan_label} SETIA BAKTI {kabupaten_label} ACEH JAYA",
        "ACEH",
    )
    assert not parsed.error
    assert (parsed.desa, parsed.kecamatan, parsed.kabupaten) == (
        "LHOK TIMON",
        "SETIA BAKTI",
        "ACEH JAYA",
    )


def test_parse_without_desa_label_when_kecamatan_and_kabupaten_are_labeled():
    parsed = parse_address("SUNGAI LANDIA KEC. IV KOTO KAB. AGAM", "SUMATERA BARAT")
    assert (parsed.desa, parsed.kecamatan, parsed.kabupaten) == (
        "SUNGAI LANDIA",
        "IV KOTO",
        "AGAM",
    )


def test_parse_dot_format():
    parsed = parse_address("DESA KEUDE LAPANG. LAPANG. ACEH UTARA", "ACEH")
    assert not parsed.error
    assert parsed.kecamatan == "LAPANG"


def test_parse_desa_and_kecamatan_without_kabupaten():
    parsed = parse_address("DESA AIR PINANG KEC. SIMEULUE TIMUR", "ACEH")
    assert (parsed.desa, parsed.kecamatan, parsed.kabupaten) == (
        "AIR PINANG",
        "SIMEULUE TIMUR",
        "",
    )


def test_parse_desa_only():
    parsed = parse_address("SIMPANG JAYA", "ACEH")
    assert (parsed.desa, parsed.kecamatan, parsed.kabupaten) == (
        "SIMPANG JAYA",
        "",
        "",
    )


def test_parse_rejang_lebong_as_complete_kabupaten_name():
    parsed = parse_address("DS. DERATI KEC. KOTA PADANG KAB. REJANG LEBONG", "BENGKULU")
    assert (parsed.desa, parsed.kecamatan, parsed.kabupaten) == (
        "DERATI",
        "KOTA PADANG",
        "REJANG LEBONG",
    )


def test_parse_pekon_as_part_of_desa_name():
    parsed = parse_address("PEKON PEJAJARAN KEC. KOTAAGUNG KAB. TANGGAMUS", "LAMPUNG")
    assert (parsed.desa, parsed.kecamatan, parsed.kabupaten) == (
        "PEKON PEJAJARAN",
        "KOTAAGUNG",
        "TANGGAMUS",
    )


def test_empty_address_still_fails_parsing():
    assert parse_address("", "ACEH").error
