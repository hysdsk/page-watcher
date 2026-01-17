from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class TriggerEvent:
    url: str
    detected_at: str
    reason: str
    last_hash: str
    extra: dict


class StateStore:
    """
    1ターゲットごとの状態を /var/lib/page-watcher/<state_key>/ に保存する想定。
    - triggered.flag が存在すれば次回以降スキップ
    - last_hash.txt は参考（ページ変化の記録）
    - triggered_event.json に検知イベントを出力
    - run.lock で多重起動を避ける（簡易）
    """

    def __init__(self, base_dir: Path, state_key: str):
        self.dir = base_dir / state_key
        self.dir.mkdir(parents=True, exist_ok=True)

        self.trigger_flag = self.dir / "triggered.flag"
        self.last_hash_file = self.dir / "last_hash.txt"
        self.last_status_file = self.dir / "last_status.txt"
        self.event_file = self.dir / "triggered_event.json"
        self.lock_file = self.dir / "run.lock"

    def is_triggered(self) -> bool:
        return self.trigger_flag.exists()

    def load_last_hash(self) -> str:
        if self.last_hash_file.exists():
            return self.last_hash_file.read_text(encoding="utf-8").strip()
        return ""

    def save_last_hash(self, h: str) -> None:
        self.last_hash_file.write_text(h, encoding="utf-8")

    def load_last_status(self) -> str:
        """前回のステータスを取得 (available/unavailable/unknown)"""
        if self.last_status_file.exists():
            return self.last_status_file.read_text(encoding="utf-8").strip()
        return "unknown"

    def save_last_status(self, status: str) -> None:
        """現在のステータスを保存 (available/unavailable)"""
        self.last_status_file.write_text(status, encoding="utf-8")

    def mark_triggered(self, event: TriggerEvent) -> None:
        self.event_file.write_text(
            json.dumps(
                {
                    "url": event.url,
                    "detected_at_utc": event.detected_at,
                    "reason": event.reason,
                    "last_hash": event.last_hash,
                    "extra": event.extra,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.trigger_flag.write_text(event.detected_at, encoding="utf-8")

    @contextmanager
    def lock(self, stale_sec: int = 3600) -> Iterator[bool]:
        """
        簡易ロック。run.lock があれば基本は実行しない。
        stale_sec より古ければ回収して実行を許可。
        """
        acquired = False
        try:
            if self.lock_file.exists():
                try:
                    age = time.time() - self.lock_file.stat().st_mtime
                    if age > stale_sec:
                        self.lock_file.unlink(missing_ok=True)
                    else:
                        yield False
                        return
                except Exception:
                    yield False
                    return

            self.lock_file.write_text(str(os.getpid()), encoding="utf-8")
            acquired = True
            yield True
        finally:
            if acquired:
                try:
                    self.lock_file.unlink(missing_ok=True)
                except Exception:
                    pass
