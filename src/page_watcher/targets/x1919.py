from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    key: str
    url: str
    block_text: str


TARGET = Target(
    key="x1919",
    url="https://www.31sumai.com/attend/X1919/",
    block_text="誠に申し訳ございませんが、ただいま予約を受け付けておりません。",
)
