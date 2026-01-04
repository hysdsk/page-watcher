from __future__ import annotations

import hashlib


def contains_block_text(html: str, block_text: str) -> bool:
    return block_text in html


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
