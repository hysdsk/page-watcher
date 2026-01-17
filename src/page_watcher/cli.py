from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta

from .config import load_config
from .fetcher import fetch_html_with_js, fetch_html_with_click
from .detectors import contains_status_td, sha256_hex, extract_mansion_name
from .state.store import StateStore, TriggerEvent
from .targets import x1919, x1413
from .notifier.discord import DiscordNotifier


def jst_now_iso() -> str:
    """日本時間(JST)の現在時刻をISO形式で返す"""
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).isoformat()


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

        # table内に status_2 または status_3 クラスの td があれば「予約受付中」
        has_status_td = contains_status_td(html)

        # 最初のページで見つからなければ、次のページ（datepicker-next）をクリックしてチェック
        if not has_status_td:
            html_next = fetch_html_with_click(
                target.url,
                user_agent=cfg.user_agent,
                timeout_sec=cfg.timeout_sec,
                click_selector="a.ui-datepicker-next",
                wait_after_click=2.0,
                wait_for_selector_after_click="tbody tr td"
            )
            has_status_td = contains_status_td(html_next)

        # 現在のステータスを判定
        current_status = "available" if has_status_td else "unavailable"
        
        # 前回のステータスを取得
        last_status = store.load_last_status()
        
        # ステータスを保存（常に更新）
        store.save_last_status(current_status)

        # ステータスが変化した場合のみ通知
        if last_status != current_status and last_status != "unknown":
            mansion_name = extract_mansion_name(html)
            
            if current_status == "available":
                reason = "STATUS_CHANGED_TO_AVAILABLE"
                note = "予約受付中に変化しました（status_2 または status_3 が検出されました）"
                msg = (
                    f"<@{cfg.discord.dsk_play_id}>\n"
                    f"「{mansion_name}」のMR予約枠に空きが出ました。\n"
                    f"予約フォーム: {target.url}\n"
                )
            else:
                reason = "STATUS_CHANGED_TO_UNAVAILABLE"
                note = "予約不可に変化しました（status_2, status_3 が存在しません）"
                msg = (
                    f"<@{cfg.discord.dsk_play_id}>\n"
                    f"「{mansion_name}」のMR予約枠が埋まりました。\n"
                    f"予約フォーム: {target.url}\n"
                )
            
            event = TriggerEvent(
                url=target.url,
                detected_at=jst_now_iso(),
                reason=reason,
                last_hash=h,
                extra={
                    "target_key": target.key,
                    "previous_status": last_status,
                    "current_status": current_status,
                    "note": note,
                },
            )
            store.mark_triggered(event)

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
