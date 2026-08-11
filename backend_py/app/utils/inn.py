"""INN / STIR normalization for Uzbek and foreign companies."""

from __future__ import annotations

import re

_UZ_INN_LEN = 9


def normalize_inn(raw: str | int | None) -> str:
    """
    Uzbek legal entity INN: 9 digits.
    Foreign IDs: keep alphanumeric string (no scientific notation in Excel).
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""

    if re.search(r"[A-Za-z]", s):
        return re.sub(r"\s+", "", s).upper()

    digits = re.sub(r"\D", "", s)
    if len(digits) == _UZ_INN_LEN:
        return digits
    if len(digits) == 14:
        return digits
    if len(digits) > _UZ_INN_LEN:
        return s if re.search(r"[A-Za-z]", s) else digits

    return digits or s


def is_placeholder_company_name(name: str | None) -> bool:
    if not name:
        return True
    n = name.strip().lower()
    return n.startswith("поставщик") or n.startswith("postavshik") or n.startswith("supplier #")


def is_generic_company_label(name: str | None, inn: str | None = None) -> bool:
    """True for 'Kompaniya 123456789' / 'Компания …' placeholders."""
    if not name or is_placeholder_company_name(name):
        return True
    n = name.strip().lower()
    if n.startswith("kompaniya ") or n.startswith("компания ") or n.startswith("company "):
        return True
    if inn:
        inn_key = normalize_inn(inn)
        digits = re.sub(r"\D", "", n)
        if inn_key and inn_key in digits and len(n) < 40:
            return True
    return False
