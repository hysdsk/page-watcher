from __future__ import annotations

import hashlib
from bs4 import BeautifulSoup


def contains_status_td(html: str) -> bool:
    """tbody tr td内に status_2 または status_3 クラスを持つ td タグが存在するか"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # tbody > tr > td の構造で status_2 または status_3 クラスを持つものを検索
        tables = soup.find_all('table')
        for table in tables:
            tbodys = table.find_all('tbody')
            for tbody in tbodys:
                trs = tbody.find_all('tr')
                for tr in trs:
                    td_tags = tr.find_all('td', class_=lambda x: x and ('status_2' in x.split() or 'status_3' in x.split()))
                    if td_tags:
                        return True
        return False
    except Exception:
        # パースエラーの場合は存在しないとみなす
        return False


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
