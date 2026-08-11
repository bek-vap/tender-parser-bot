"""Resolve UZEX etender internal trade id (same rules as /check_inn)."""

from __future__ import annotations

import re

_ETENDER_LOT_URL = re.compile(r"etender\.uzex\.uz/lot/(\d+)", re.I)


def resolve_uzex_trade_id(
    external_id: str | int | None = None,
    url: str | None = None,
) -> int | None:
    """
    Map DB external_id / lot URL to API trade id (e.g. 486901).

    /check_inn uses last 6 digits for 14-digit display numbers;
    short lot numbers and /lot/{id} URLs use the internal id directly.
    """
    if url:
        m = _ETENDER_LOT_URL.search(url)
        if m:
            tid = int(m.group(1))
            if tid < 10_000_000:
                return tid

    if external_id is None:
        return None

    s = str(external_id).strip()
    if not s.isdigit():
        return None

    if len(s) <= 8:
        return int(s)

    if len(s) >= 12:
        return int(s[-6:])

    return int(s)
