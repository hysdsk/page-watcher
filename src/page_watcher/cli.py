from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta

from .config import load_config
from .fetcher import fetch_html_with_js
from .detectors import contains_status_td, sha256_hex
from .state.store import StateStore, TriggerEvent
from .targets import x1919, x1413
from .notifier.discord import DiscordNotifier


def jst_now_iso() -> str:
    """日本時間(JST)の現在時刻をISO形式で返す"""
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).isoformat()


def iso_to_readable(iso_str: str) -> str:
    """ISO形式の日時文字列を yyyy/mm/dd hh:MM:SS 形式に変換"""
    dt = datetime.fromisoformat(iso_str)
    return dt.strftime("%Y/%m/%d %H:%M:%S")


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="page-watcher")
    p.add_argument(
        "--target",
        default="x1919",
        choices=["x1919", "x1413"],
        help="監視ターゲット",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="trigger済みでも強制実行（通知は通常通り）",
    )
    p.add_argument(
        "--no-notify",
        action="store_true",
        help="通知を送らない（状態更新とファイル出力は行う）",
    )
    return p


def main() -> int:
    args = build_argparser().parse_args()
    cfg = load_config()

    # ターゲット選択
    if args.target == "x1919":
        target = x1919.TARGET
    elif args.target == "x1413":
        target = x1413.TARGET
    else:
        raise SystemExit(f"Unknown target: {args.target}")

    store = StateStore(cfg.state_base_dir, target.key)

    if store.is_triggered() and not args.force:
        return 0

    with store.lock() as ok:
        if not ok:
            return 0

        html = fetch_html_with_js(
            target.url,
            user_agent=cfg.user_agent,
            timeout_sec=cfg.timeout_sec,
            wait_for_selector="tbody tr td",  # JS実行後のtbodyが描画されるまで待機
            wait_time=3.0
        )
        h = sha256_hex(html)

        last_h = store.load_last_hash()
        if h != last_h:
            store.save_last_hash(h)

        # table内に status_2 または status_3 クラスの td があれば「変化検知」
        has_status_td = contains_status_td(html)

        if has_status_td:
            event = TriggerEvent(
                url=target.url,
                detected_at=jst_now_iso(),
                reason="STATUS_TD_FOUND",
                last_hash=h,
                extra={
                    "target_key": target.key,
                    "note": "status_2 または status_3 のステータスが見つかりました。ページを確認してください。",
                },
            )
            store.mark_triggered(event)

            formatted_detected_at = iso_to_readable(event.detected_at)
            msg = (
                f"<@{cfg.discord.dsk_play_id}>\n"
                f"{formatted_detected_at} にページの表示が変わった可能性があります。\n"
                f"url: {target.url}\n"
            )

            if not args.no_notify:
                # Discord
                if cfg.discord is not None:
                    try:
                        DiscordNotifier(cfg.discord.webhook_url).notify(msg)
                    except Exception as e:
                        print(f"Discord notify failed: {e}")

        return 0


if __name__ == "__main__":
    raise SystemExit(main())
