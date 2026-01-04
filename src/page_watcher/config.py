from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiscordConfig:
    webhook_url: str
    dsk_play_id: str


@dataclass(frozen=True)
class AppConfig:
    state_base_dir: Path
    user_agent: str
    timeout_sec: int
    discord: DiscordConfig | None


def _getenv(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    return v.strip() if v is not None else default


def load_config() -> AppConfig:
    # 状態保存先（cronでも書き込める場所に）
    state_base_dir = Path(_getenv("STATE_BASE_DIR"))

    user_agent = _getenv(
        "USER_AGENT",
        "Mozilla/5.0 (X1919Watcher/0.1; +https://example.invalid/)"
    )
    timeout_sec = int(_getenv("HTTP_TIMEOUT_SEC", "20"))

    discord_channel_id = _getenv("DISCORD_CHANNEL_ID")
    discord_webhook_token = _getenv("DISCORD_WEBHOOK_TOKEN")
    discord_webhook_url = f"https://discord.com/api/webhooks/{discord_channel_id}/{discord_webhook_token}"
    dsk_play_id = _getenv("DSK_PLAY_ID")
    discord = DiscordConfig(webhook_url=discord_webhook_url, dsk_play_id=dsk_play_id) if discord_webhook_url else None

    return AppConfig(
        state_base_dir=state_base_dir,
        user_agent=user_agent,
        timeout_sec=timeout_sec,
        discord=discord,
    )
