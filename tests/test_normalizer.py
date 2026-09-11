from koperasi_match.normalizer import aliases, normalize_header, normalize_kabupaten, normalize_name


def test_normalization_and_aliases():
    assert normalize_header(" Kota/Kabupaten\n") == "KOTAKABUPATEN"
    assert normalize_name("PROVINSI NAD", kind="province") == "ACEH"
    assert normalize_name("Aceh (NAD)", kind="province") == "ACEH"
    assert normalize_name("SUMUT", kind="province") == "SUMATERA UTARA"
    assert normalize_name("Bangka Belitung", kind="province") == "KEPULAUAN BANGKA BELITUNG"
    assert (
        normalize_name("Kepulauan Bangka Belitung", kind="province") == "KEPULAUAN BANGKA BELITUNG"
    )
    assert normalize_kabupaten("Kabupaten Langkat") == "LANGKAT"
    assert normalize_kabupaten("Kota Langsa") == "LANGSA"
    assert normalize_kabupaten("Kota Rejang Lebong") == "REJANG LEBONG"
    assert aliases("Jati Kusuma (Kesuma)", kind="desa") == ("JATI KUSUMA", "KESUMA")
    assert aliases("Pekon Pejajaran", kind="desa") == (
        "PEKON PEJAJARAN",
        "PEJAJARAN",
    )
    assert normalize_name("DES. Layeun", kind="desa") == "LAYEUN"


def test_identifiers_keep_apostrophe_and_roman_number():
    assert normalize_name("Maliwa'a", kind="desa") == "MALIWA'A"
    assert normalize_name("Pasar VIII", kind="desa") == "PASAR VIII"
