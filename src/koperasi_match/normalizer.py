import re
import unicodedata

PROVINCE_ALIASES = {
    "NAD": "ACEH",
    "PROVINSI NAD": "ACEH",
    "PROVINSI ACEH": "ACEH",
    "SUMUT": "SUMATERA UTARA",
    "PROVINSI SUMUT": "SUMATERA UTARA",
    "PROVINSI SUMATRA UTARA": "SUMATERA UTARA",
    "BANGKA BELITUNG": "KEPULAUAN BANGKA BELITUNG",
    "PROVINSI BANGKA BELITUNG": "KEPULAUAN BANGKA BELITUNG",
}

REGION_ALIASES = {
    "TAPUT": "TAPANULI UTARA",
}


def _ascii_upper(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not unicodedata.combining(char)).upper()


def clean_spaces(value: object) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def normalize_header(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", "", _ascii_upper(value))


def normalize_name(value: object, *, kind: str = "generic") -> str:
    text = _ascii_upper(value)
    if kind == "province":
        text = re.sub(r"\([^)]*\)", " ", text)
        text = PROVINCE_ALIASES.get(clean_spaces(text), text)
    prefixes = {
        "desa": r"\b(?:DESA|DES|DS|KELURAHAN|KEL)\.?\s*",
        "kecamatan": r"\b(?:KECAMATAN|KEC)\.?\s*",
        "kabupaten": r"\b(?:KABUPATEN|KAB|KOTA)\.?\s*",
        "province": r"\bPROVINSI\s*",
    }
    if kind in prefixes:
        text = re.sub(prefixes[kind], " ", text)
    text = re.sub(r"[^A-Z0-9']+", " ", text)
    text = " ".join(text.split())
    if kind == "province":
        text = PROVINCE_ALIASES.get(text, text)
    return REGION_ALIASES.get(text, text)


def aliases(value: object, *, kind: str = "generic") -> tuple[str, ...]:
    raw = clean_spaces(value)
    without_parentheses = re.sub(r"\([^)]*\)", " ", raw)
    candidates = [without_parentheses]
    for inside in re.findall(r"\(([^)]+)\)", raw):
        candidates.extend(re.split(r"\s*/\s*", inside))
    candidates.extend(re.split(r"\s*/\s*", without_parentheses))
    normalized = []
    for candidate in candidates:
        item = normalize_name(candidate, kind=kind)
        if item and item not in normalized:
            normalized.append(item)
        if kind == "desa" and item.startswith("PEKON "):
            without_pekon = item.removeprefix("PEKON ").strip()
            if without_pekon and without_pekon not in normalized:
                normalized.append(without_pekon)
    return tuple(normalized)


def normalize_kabupaten(value: object) -> str:
    text = normalize_name(value, kind="kabupaten")
    return REGION_ALIASES.get(text, text)
