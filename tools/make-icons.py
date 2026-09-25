"""ファビコン一式を作る。

図柄: インクの角丸四角に、白いフキダシとピンクの「ON AIR」ランプ(ヘッダーのロゴと同じ点)。
周りの短い線は集中線の名残で、16px では消えてフキダシと点だけが残るように細くしてある。
SVG と PNG/ICO を同じ座標(64x64 基準)から書き出す。要 Pillow。
    python tools/make-icons.py

出力(public/):
  favicon.svg           … ふつうのブラウザ用
  favicon.ico           … 16/32/48px(SVG 非対応の環境・検索結果用)
  apple-touch-icon.png  … 180px(iOS のホーム画面)
  icon-192.png / icon-512.png … Android・PWA 用
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "public"
INK = "#15172B"
PAPER = "#F2F3F7"
ONAIR = "#E8195A"

# 64x64 基準の図形
RADIUS = 14
BUBBLE = (32, 29, 21, 16)  # cx, cy, rx, ry
TAIL = [(21, 38), (31, 42), (17, 53)]
LAMP = (32, 29, 6.5)
# 集中線: 四隅寄りに8本
RAYS = [(math.radians(a), 25.5, 30.5) for a in (-160, -110, -70, -20, 20, 70, 110, 160)]
RAY_CENTER = (32, 31)


def svg() -> str:
    cx, cy, rx, ry = BUBBLE
    lx, ly, lr = LAMP
    rays = "".join(
        f'<path d="M{RAY_CENTER[0] + math.cos(a) * r1:.1f} {RAY_CENTER[1] + math.sin(a) * r1:.1f}'
        f'L{RAY_CENTER[0] + math.cos(a) * r2:.1f} {RAY_CENTER[1] + math.sin(a) * r2:.1f}"/>'
        for a, r1, r2 in RAYS
    )
    tail = " ".join(f"{x},{y}" for x, y in TAIL)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="{RADIUS}" fill="{INK}"/>'
        f'<g stroke="{ONAIR}" stroke-width="2.4" stroke-linecap="round" opacity=".85">{rays}</g>'
        f'<polygon points="{tail}" fill="{PAPER}"/>'
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{PAPER}"/>'
        f'<circle cx="{lx}" cy="{ly}" r="{lr}" fill="{ONAIR}"/>'
        "</svg>\n"
    )


def png(size: int, rays: bool = True, rounded: bool = True) -> Image.Image:
    ss = 8  # 8倍で描いて縮小
    k = size * ss / 64
    img = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle((0, 0, size * ss - 1, size * ss - 1), RADIUS * k, fill=INK)
    else:
        d.rectangle((0, 0, size * ss, size * ss), fill=INK)
    if rays:
        for a, r1, r2 in RAYS:
            p1 = (RAY_CENTER[0] + math.cos(a) * r1, RAY_CENTER[1] + math.sin(a) * r1)
            p2 = (RAY_CENTER[0] + math.cos(a) * r2, RAY_CENTER[1] + math.sin(a) * r2)
            w = 2.4 * k
            d.line([(p1[0] * k, p1[1] * k), (p2[0] * k, p2[1] * k)], fill=ONAIR, width=round(w))
            for px, py in (p1, p2):
                d.ellipse((px * k - w / 2, py * k - w / 2, px * k + w / 2, py * k + w / 2), fill=ONAIR)
    d.polygon([(x * k, y * k) for x, y in TAIL], fill=PAPER)
    cx, cy, rx, ry = BUBBLE
    d.ellipse(((cx - rx) * k, (cy - ry) * k, (cx + rx) * k, (cy + ry) * k), fill=PAPER)
    lx, ly, lr = LAMP
    d.ellipse(((lx - lr) * k, (ly - lr) * k, (lx + lr) * k, (ly + lr) * k), fill=ONAIR)
    return img.resize((size, size), Image.LANCZOS)


(OUT / "favicon.svg").write_text(svg(), encoding="utf-8")
# 16px では集中線がにじむだけなので消す
# Pillow は基準画像より大きいサイズを書かないので、48px を基準にして 16/32px を添える
png(48).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[png(16, rays=False), png(32)])
# iOS は自分で角を丸めるので、四角いまま塗りつぶす
png(180, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
png(192).save(OUT / "icon-192.png", optimize=True)
png(512).save(OUT / "icon-512.png", optimize=True)
for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
    print(name, (OUT / name).stat().st_size)
