from __future__ import annotations

import discord


class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, message: str) -> None:
        # cron等の同期実行に向いている
        webhook = discord.SyncWebhook.from_url(self.webhook_url)
        webhook.send(content=message)
