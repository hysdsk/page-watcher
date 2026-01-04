from __future__ import annotations

import time
import requests


def fetch_html(url: str, *, user_agent: str, timeout_sec: int, retries: int = 2) -> str:
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "ja,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout_sec)
            r.raise_for_status()
            if r.encoding is None:
                r.encoding = "utf-8"
            return r.text
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(1.0 + attempt)  # 軽いバックオフ
            else:
                raise

    # ここには来ないが型のため
    assert last_exc is not None
    raise last_exc
