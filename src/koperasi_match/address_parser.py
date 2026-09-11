import re

from .models import ParsedAddress
from .normalizer import aliases, clean_spaces, normalize_kabupaten, normalize_name

LABEL_PATTERN = re.compile(
    r"^(?:KDKMP\s+)?"
    r"(?:(?:DESA|DES|DS|KELURAHAN|KEL)\s*[.,]?\s*)?"
    r"(?P<desa>.*?)\s*[,;]?\s*"
    r"(?:KECAMATAN|KEC)\s*[.,]?\s*"
    r"(?P<kecamatan>.*?)\s*[,;]?\s*"
    r"(?P<type>KABUPATEN|KAB|KOTA(?!.*\b(?:KABUPATEN|KAB)\b))\b\s*[.,]?\s*"
    r"(?P<kabupaten>.+)$",
    re.IGNORECASE,
)

DESA_KECAMATAN_PATTERN = re.compile(
    r"^(?:KDKMP\s+)?"
    r"(?:(?:DESA|DES|DS|KELURAHAN|KEL)\s*[.,]?\s*)?"
    r"(?P<desa>.*?)\s*[,;]?\s*"
    r"(?:KECAMATAN|KEC)\s*[.,]?\s*"
    r"(?P<kecamatan>.+)$",
    re.IGNORECASE,
)


def _build(
    original: str, desa: str, kecamatan: str, kabupaten: str, province: str
) -> ParsedAddress:
    desa_aliases = aliases(desa, kind="desa")
    kec_aliases = aliases(kecamatan, kind="kecamatan")
    kab_aliases = aliases(kabupaten, kind="kabupaten")
    return ParsedAddress(
        original=original,
        desa=desa_aliases[0] if desa_aliases else "",
        kecamatan=kec_aliases[0] if kec_aliases else "",
        kabupaten=normalize_kabupaten(kabupaten),
        province=normalize_name(province, kind="province"),
        desa_aliases=desa_aliases,
        kecamatan_aliases=kec_aliases,
        kabupaten_aliases=kab_aliases,
    )


def parse_address(address: object, province: str = "") -> ParsedAddress:
    original = clean_spaces(address)
    if not original:
        return ParsedAddress(original="", province=province, error="Alamat kosong")

    match = LABEL_PATTERN.match(original)
    if match:
        kabupaten = match.group("kabupaten")
        if match.group("type") and match.group("type").upper() == "KOTA":
            kabupaten = f"KOTA {kabupaten}"
        return _build(original, match.group("desa"), match.group("kecamatan"), kabupaten, province)

    desa_kecamatan_match = DESA_KECAMATAN_PATTERN.match(original)
    if desa_kecamatan_match:
        return _build(
            original,
            desa_kecamatan_match.group("desa"),
            desa_kecamatan_match.group("kecamatan"),
            "",
            province,
        )

    parts = [part.strip(" .") for part in original.split(",") if part.strip(" .")]
    if len(parts) >= 3:
        return _build(original, parts[0], parts[1], parts[2], province)

    dotted = [part.strip() for part in re.split(r"\.(?:\s+|(?=[A-Z]))", original) if part.strip()]
    if len(dotted) == 3:
        return _build(original, dotted[0], dotted[1], dotted[2], province)

    if len(parts) == 2:
        return _build(original, parts[0], parts[1], "", province)

    if len(parts) == 1:
        return _build(original, parts[0], "", "", province)

    return ParsedAddress(
        original=original,
        province=normalize_name(province, kind="province"),
        error="Format alamat tidak dapat dipisahkan",
    )
