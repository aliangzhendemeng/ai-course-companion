"""录屏功能展示（每个 5-10s）：Playwright 录视频 → ffmpeg 转 mp4。

前置：后端（localhost:8000）+ 前端（localhost:3000）运行；本机装 ffmpeg。
跑法：cd showcase && python3 scripts/gen_videos.py
输出：public/videos/*.mp4
"""
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "public" / "videos"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://localhost:3000"


def click_tab(page, name):
    try:
        page.get_by_role("tab", name=name).click(timeout=2500)
        page.wait_for_timeout(1200)
    except Exception:
        pass


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("pip install playwright && playwright install chromium"); sys.exit(1)
    if not shutil.which("ffmpeg"):
        print("需要 ffmpeg 转 mp4"); sys.exit(1)

    clips = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, record_video_dir=str(OUT))

        def record(name, url, fn, ms):
            page = ctx.new_page()
            try:
                page.goto(f"{BASE}{url}", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                fn(page)
                page.wait_for_timeout(ms)
                src = page.video.path()
                page.close()
                mp4 = OUT / f"{name}.mp4"
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf",
                                "scale=1024:-2,fps=15", str(mp4)], check=True)
                Path(src).unlink(missing_ok=True)
                clips.append(name)
                print(f"✓ {name}.mp4")
            except Exception as e:
                print(f"✗ {name}: {e}")
                page.close()

        # 1. 课程库（滚动展示仪表盘/周报/打卡）
        record("courses", "/courses", lambda pg: pg.evaluate("window.scrollTo(0, 400);"), 4000)

        # 2. 课程详情（切测验 Tab）
        record("quiz", "/courses/1", lambda pg: click_tab(pg, "测验"), 4000)

        # 3. 闪卡（切闪卡 + 翻卡）
        def flip(pg):
            click_tab(pg, "闪卡")
            try: pg.get_by_role("button", name="背面").click(timeout=1500)
            except: pass
        record("flashcard", "/courses/1", flip, 4000)

        # 4. 笔记（切笔记 Tab）
        record("notes", "/courses/1", lambda pg: click_tab(pg, "笔记"), 3000)

        # 5. 问答历史
        record("history", "/history", lambda pg: pg.evaluate("window.scrollTo(0, 200);"), 3000)

        # 6. 视频播放 + 字幕
        def play_video(pg):
            pg.evaluate("const v=document.querySelector('video'); if(v){v.muted=true;v.currentTime=10;v.play();}")
        record("video", "/courses/1", play_video, 5000)

        # 7. 错题本（测验 Tab 内切错题本）
        def wrongbook(pg):
            click_tab(pg, "测验")
            try: pg.get_by_text("错题本").first.click(timeout=2000)
            except: pass
        record("wrongbook", "/courses/1", wrongbook, 4000)

        # 8. 智能问答 + 联网搜索
        def chat(pg):
            try:
                pg.locator("button[title*='联网']").click(timeout=1500)  # 开联网
                pg.fill("textarea", "什么是大数据")
                pg.keyboard.press("Enter")
            except: pass
        record("chat", "/courses/1", chat, 13000)

        # 8.5 视频上传 / 链接导入（上传 Modal + 切链接 Tab + 粘 URL）
        def upload(pg):
            try:
                pg.get_by_role("button", name="上传课程").click(timeout=2000)
                pg.wait_for_timeout(1500)
                pg.get_by_text("链接导入").click(timeout=1500)
                pg.wait_for_timeout(1000)
                pg.locator("#url").fill("https://www.bilibili.com/video/BV1xxxxxx")
                pg.wait_for_timeout(1500)
            except: pass
        record("upload", "/courses", upload, 8000)

        # 9. 咕咕嘎嘎学伴：screenshot clip 序列锁定学伴区域（保证学伴在画面）→ ffmpeg 合成
        page = ctx.new_page()
        try:
            page.goto(f"{BASE}/courses/1", wait_until="domcontentloaded", timeout=15000)
            page.evaluate("localStorage.removeItem('companion.pos')")
            page.reload()
            page.wait_for_timeout(1500)
            # 学伴区域 clip（基于实测 bounding_box：学伴+气泡 x≈985-1290 y≈540-805）
            clip = {"x": 985, "y": 540, "width": 305, "height": 265}
            for f in glob.glob("/tmp/cf_*.png"):
                os.remove(f)
            n = 0
            for mood, key in [("happy", "greeting"), ("celebrate", "celebrate"), ("confused", "wrong")]:
                page.evaluate(f"window.__react && window.__react('{mood}','{key}',false)")
                for _ in range(10):
                    page.wait_for_timeout(250)
                    page.screenshot(path=f"/tmp/cf_{n:03d}.png", clip=clip)
                    n += 1
            # 拖动帧
            try:
                img = page.locator("img[alt='咕咕嘎嘎']").first
                if img.count():
                    box = img.bounding_box()
                    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    page.mouse.down()
                    page.mouse.move(box["x"] - 60, box["y"] - 30, steps=6)
                    page.mouse.up()
                    for _ in range(8):
                        page.wait_for_timeout(250)
                        page.screenshot(path=f"/tmp/cf_{n:03d}.png", clip=clip)
                        n += 1
            except Exception:
                pass
            page.close()
            mp4 = OUT / "companion.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "4",
                            "-i", "/tmp/cf_%03d.png",
                            "-vf", "scale=900:780,fps=15", "-pix_fmt", "yuv420p", str(mp4)], check=True)
            for f in glob.glob("/tmp/cf_*.png"):
                os.remove(f)
            print(f"✓ companion.mp4 (clip 序列，{n} 帧)")
        except Exception as e:
            print(f"✗ companion: {e}")
            page.close()

        browser.close()

    print(f"\n录屏完成 {len(clips)} 段 → {OUT}")
    print("在 index.astro 用 <video autoplay loop muted playsinline src=\"/videos/X.mp4\"></video> 嵌入")


if __name__ == "__main__":
    main()
