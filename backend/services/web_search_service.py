"""网络查询服务：用 Playwright headless 浏览器搜索百度，抓取结果。

重要：Playwright sync API 在 FastAPI 同步端点的线程池里会卡死（event loop 冲突），
故把搜索逻辑放子进程跑（_search_sync），主进程通过 subprocess 调用。

百度国内可访问；反爬用 UA + 隐藏 webdriver 缓解。失败返回空列表，不阻断问答。
"""

import json
import logging
import subprocess
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from backend.config import settings

logger = logging.getLogger(__name__)

SEARCH_TIMEOUT_MS = 20000


def _search_sync(query: str, n: int = 5) -> list[dict]:
    """实际搜索逻辑（在子进程跑，避免与 FastAPI 线程池 event loop 冲突）。"""
    url = f"https://www.baidu.com/s?wd={quote(query)}"
    results: list[dict] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, args=["--disable-blink-features=AutomationDetected"]
            )
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
            )
            page.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )
            page.goto(url, timeout=SEARCH_TIMEOUT_MS, wait_until="domcontentloaded")
            try:
                page.wait_for_selector("div.c-container, div.result", timeout=8000)
            except Exception:
                pass
            blocks = page.query_selector_all("div.c-container, div.result, div[data-tu]")
            for block in blocks:
                if len(results) >= n:
                    break
                try:
                    link = block.query_selector("h3 a") or block.query_selector("a[href]")
                    title_el = block.query_selector("h3")
                    if not link or not title_el:
                        continue
                    href = link.get_attribute("href") or ""
                    title = title_el.inner_text().strip()
                    if not title or not href:
                        continue
                    snippet = ""
                    for sel in (".c-abstract", "span.content-right_8Zs40", "span"):
                        snip_el = block.query_selector(sel)
                        if snip_el:
                            t = snip_el.inner_text().strip()
                            if t and len(t) > 15:
                                snippet = t
                                break
                    results.append({"title": title, "url": href, "snippet": snippet})
                except Exception:
                    continue
            browser.close()
    except Exception as e:
        logger.warning("网络查询失败（百度反爬或网络问题）: %s", e)
    return results


class WebSearchService:
    """百度搜索（通过子进程跑 Playwright，避免 event loop 冲突）。"""

    def search(self, query: str, n: int = 5) -> list[dict]:
        """搜索 query，返回前 n 条 [{title, url, snippet}]。失败返回空列表。"""
        if not query.strip():
            return []
        code = (
            "from backend.services.web_search_service import _search_sync; "
            "import json; "
            f"print(json.dumps(_search_sync({query!r}, {n}), ensure_ascii=False))"
        )
        try:
            r = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=40,
                cwd=str(settings.project_root),
            )
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout.strip().splitlines()[-1])
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning("网络查询子进程失败: %s", e)
        return []
