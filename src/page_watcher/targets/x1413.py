from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    key: str
    url: str


TARGET = Target(
    key="x1413",
    url="https://www.31sumai.com/attend/X1413/",
)
