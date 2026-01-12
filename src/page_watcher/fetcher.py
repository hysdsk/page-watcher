from __future__ import annotations

import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


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


def fetch_html_with_js(
    url: str,
    *,
    user_agent: str,
    timeout_sec: int,
    wait_for_selector: str | None = None,
    wait_time: float = 2.0,
    retries: int = 2
) -> str:
    """
    PlaywrightでJavaScript実行後のHTMLを取得
    
    Args:
        url: 取得するURL
        user_agent: User-Agentヘッダー
        timeout_sec: タイムアウト秒数
        wait_for_selector: 待機するCSSセレクタ（Noneの場合は固定時間待機）
        wait_time: wait_for_selectorがNoneの場合の待機時間（秒）
        retries: リトライ回数
    """
    last_exc: Exception | None = None
    
    for attempt in range(retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=user_agent,
                    locale='ja-JP',
                    viewport={'width': 1280, 'height': 720}
                )
                page = context.new_page()
                
                # ページを開く
                page.goto(url, timeout=timeout_sec * 1000, wait_until='networkidle')
                
                # 特定の要素が表示されるまで待機、またはJSの実行を待つ
                if wait_for_selector:
                    page.wait_for_selector(wait_for_selector, timeout=timeout_sec * 1000)
                else:
                    time.sleep(wait_time)
                
                # HTMLを取得
                html = page.content()
                
                browser.close()
                return html
                
        except (PlaywrightTimeout, Exception) as e:
            last_exc = e
            if attempt < retries:
                time.sleep(1.0 + attempt)
            else:
                raise
    
    assert last_exc is not None
    raise last_exc
