"""Human-readable UZS amounts for Excel and bot messages."""

from __future__ import annotations

import re


def parse_amount_number(raw: str | int | float | None) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip()
    if not s:
        return None
    cleaned = re.sub(r"[^\d.,]", "", s.replace(" ", ""))
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = parts[0] + "." + parts[1]
        else:
            cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def format_uzs_short(amount: float | None) -> str:
    """e.g. 1.23 mlrd UZS | 45.6 mln UZS | 850 000 UZS"""
    if amount is None or amount <= 0:
        return "—"
    if amount >= 1_000_000_000:
        val = amount / 1_000_000_000
        return f"{val:.2f} mlrd UZS"
    if amount >= 1_000_000:
        val = amount / 1_000_000
        return f"{val:.1f} mln UZS"
    whole = int(round(amount))
    s = f"{whole:,}".replace(",", " ")
    return f"{s} UZS"


def format_uzs_total(amount: float | None) -> str:
    """Total line: full number + short hint in parentheses."""
    if amount is None or amount <= 0:
        return "—"
    whole = int(round(amount))
    full = f"{whole:,}".replace(",", " ")
    short = format_uzs_short(amount)
    if short.startswith(full):
        return short
    return f"{full} UZS ({short})"
