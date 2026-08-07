#!/usr/bin/env python3
"""把 Astro 构建产物打包成单文件 HTML：CSS 内联，视频 base64 嵌入。

只嵌入 index.html 里实际引用的视频（data-video 指向的 9 个），
未被引用的（如 diagnose.mp4 / wrongbook.mp4）跳过，避免体积浪费。
"""

import base64
import re
from pathlib import Path

DIST = Path(__file__).parent.parent / "dist"
OUT = Path(__file__).parent.parent / "ai-course-companion-showcase.html"


def inline_css(html: str) -> str:
    for css_file in (DIST / "_astro").glob("*.css"):
        css = css_file.read_text(encoding="utf-8")
        # <link rel="stylesheet" href="/_astro/xxx.css">（属性顺序可能不同）
        pattern = rf'<link[^>]*href="[^"]*{re.escape(css_file.name)}"[^>]*/?>'
        html, n = re.subn(pattern, lambda m: f"<style>{css}</style>", html)
        print(f"  CSS {css_file.name}: {'内联' if n else '未找到引用'}")
    return html


def embed_videos(html: str) -> str:
    # 收集页面里真实引用到的视频文件名
    referenced = set(re.findall(r'data-video="[^"]*?videos/([^"/]+\.mp4)"', html))
    print(f"  页面引用 {len(referenced)} 个视频")
    for name in sorted(referenced):
        src = DIST / "videos" / name
        if not src.exists():
            print(f"  ⚠ 缺失 {name}")
            continue
        b64 = base64.b64encode(src.read_bytes()).decode("utf-8")
        data_url = f"data:video/mp4;base64,{b64}"
        # 替换所有形如 "./videos/name"、"videos/name"、"/videos/name" 的引用
        pattern = rf'"(?:\.?/)?videos/{re.escape(name)}"'
        html, n = re.subn(pattern, f'"{data_url}"', html)
        kb = src.stat().st_size / 1024
        print(f"  ✓ {name}（{kb:.0f} KB，替换 {n} 处）")
    return html


def main():
    html_path = DIST / "index.html"
    if not html_path.exists():
        print("错误：dist/index.html 不存在，请先运行 npm run build")
        return
    html = html_path.read_text(encoding="utf-8")

    print("内联 CSS…")
    html = inline_css(html)
    print("嵌入视频…")
    html = embed_videos(html)

    # 清理残留的 _astro 引用（保险）
    html = re.sub(r'\s*<link[^>]*href="/?_astro/[^"]*"[^>]*/?>', "", html)
    html = re.sub(r'\s*<script[^>]*src="/?_astro/[^"]*"[^>]*></script>', "", html)

    OUT.write_text(html, encoding="utf-8")
    mb = OUT.stat().st_size / (1024 * 1024)
    print(f"\n✓ 生成单文件：{OUT.name}（{mb:.1f} MB）")


if __name__ == "__main__":
    main()
