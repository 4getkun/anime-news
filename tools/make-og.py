"""共有カード画像 public/og-image.png (1200x630) を作る。

サイトのヒーローと同じ「集中線＋網点＋フキダシ」の絵柄。手元で1回動かしてコミットする
(ビルド時には動かない)。要 Pillow。フォントは Windows 標準の BIZ UDゴシック Bold。
    python tools/make-og.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
INK = (21, 23, 43)
PAPER = (242, 243, 247)
ONAIR = (232, 25, 90)
MARKER = (255, 225, 74)
FONT = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"
OUT = Path(__file__).resolve().parent.parent / "public" / "og-image.png"

img = Image.new("RGB", (W, H), INK)
draw = ImageDraw.Draw(img, "RGBA")

# 網点(周辺ほど濃い)
cx, cy = W * 0.72, H * 0.46
for y in range(0, H, 9):
    for x in range(0, W, 9):
        d = math.hypot(x - cx, y - cy) / math.hypot(W, H)
        if d > 0.18:
            a = int(min(1, (d - 0.18) / 0.4) * 40)
            draw.ellipse((x - 1.4, y - 1.4, x + 1.4, y + 1.4), fill=(*PAPER, a))

# 集中線
random.seed(7)
R = math.hypot(W, H)
for i in range(170):
    ang = i / 170 * math.tau + random.random() * 0.03
    width = 0.004 + random.random() * 0.012
    inner = 170 + random.random() * 150
    pts = [
        (cx + math.cos(ang - width) * R, cy + math.sin(ang - width) * R),
        (cx + math.cos(ang) * inner, cy + math.sin(ang) * inner),
        (cx + math.cos(ang + width) * R, cy + math.sin(ang + width) * R),
    ]
    draw.polygon(pts, fill=(*PAPER, 70))

title = ImageFont.truetype(FONT, 92)
small = ImageFont.truetype(FONT, 30)
bubble_font = ImageFont.truetype(FONT, 34)

draw.text((72, 110), "アニメのニュース、", font=title, fill=PAPER)
draw.text((72, 222), "ぜんぶ読む。", font=title, fill=PAPER)

# フキダシ
bx, by, bw, bh = 72, 380, 640, 130
draw.rounded_rectangle((bx + 8, by + 8, bx + bw + 8, by + bh + 8), 26, fill=ONAIR)
draw.rounded_rectangle((bx, by, bx + bw, by + bh), 26, fill=PAPER)
draw.polygon([(bx + 40, by + bh - 2), (bx + 76, by + bh - 2), (bx + 44, by + bh + 26)], fill=PAPER)
draw.text((bx + 30, by + 22), "アニメ専門媒体からGoogleニュースまで", font=small, fill=ONAIR)
draw.text((bx + 30, by + 66), "転載はまとめて、推し作品で絞れる", font=bubble_font, fill=INK)

# 右上のロゴ札
logo_font = ImageFont.truetype(FONT, 26)
logo_w = draw.textlength("アニメニュース全部", font=logo_font)
lx = W - 72 - (logo_w + 76)
draw.rounded_rectangle((lx, 70, W - 72, 128), 14, fill=MARKER)
draw.ellipse((lx + 22, 90, lx + 40, 108), fill=ONAIR)
draw.text((lx + 54, 82), "アニメニュース全部", font=logo_font, fill=INK)

# 下の速報帯
draw.rectangle((0, H - 62, W, H), fill=(12, 13, 26))
draw.rectangle((0, H - 62, W, H - 59), fill=ONAIR)
draw.rectangle((0, H - 59, 120, H), fill=ONAIR)
draw.text((26, H - 50), "速報", font=small, fill=(255, 255, 255))
draw.text((148, H - 50), "新作発表・放送・PV・キャスト・劇場版・グッズ … 1時間ごとに更新", font=ImageFont.truetype(FONT, 26), fill=PAPER)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, optimize=True)
print(OUT, OUT.stat().st_size)
