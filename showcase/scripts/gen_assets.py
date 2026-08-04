"""自动截图/录屏：访问项目各页，生成展示素材。

前置：后端（localhost:8000）+ 前端（localhost:3000）需已运行。
跑法：cd showcase && python3 scripts/gen_assets.py
输出：public/screenshots/*.png（录视频转 GIF 见文末说明）
"""
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "public"
SHOTS = OUT / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)

BASE = "http://localhost:3000"

# (文件名, 路径, 等待毫秒, 操作可选)
SHOTS_CFG = [
    ("courses", "/courses", 4000, None),          # 课程库：仪表盘+周报+打卡
    ("course-video", "/courses/1", 5000, "video"), # 课程详情：视频+总结Tab
    ("quiz", "/courses/1", 4000, "quiz"),          # 测验Tab
    ("flashcard", "/courses/1", 4000, "flashcard"),# 闪卡Tab
    ("notes", "/courses/1", 3000, "notes"),        # 笔记Tab
    ("history", "/history", 3000, None),           # 问答历史
    ("settings", "/settings", 2000, None),         # 设置
]


def click_tab(page, tab: str):
    """点课程页顶部 Tab。"""
    try:
        page.get_by_role("tab", name=tab).click(timeout=2000)
        page.wait_for_timeout(1500)
    except Exception:
        pass


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("请先安装 playwright: pip install playwright && playwright install chromium")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, path, wait, action in SHOTS_CFG:
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            try:
                page.goto(f"{BASE}{path}", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(wait)
                if action and action not in ("video",):
                    click_tab(page, {"quiz": "测验", "flashcard": "闪卡", "notes": "笔记"}.get(action, ""))
                # 滚到可视区
                page.evaluate("window.scrollTo(0, 0)")
                page.screenshot(path=str(SHOTS / f"{name}.png"), full_page=False)
                print(f"✓ {name}.png")
            except Exception as e:
                print(f"✗ {name} 失败: {e}（确认前端在 localhost:3000 运行）")
            finally:
                page.close()
        browser.close()
    print(f"\n截图保存到 {SHOTS}")


if __name__ == "__main__":
    main()
