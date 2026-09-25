"""共有カード画像 public/og-image.png (1200x630) を作る。

サイトのヒーローと同じ「マンガの1コマ」の絵柄: 夜のインク地に集中線と網点、
サイト名を描き文字(効果音)のように組み、右に機能を3つのフキダシで並べる。
手元で1回動かしてコミットする(ビルド時には動かない)。要 Pillow。
    python tools/make-og.py

フォント: 見出しは tools/fonts/DelaGothicOne-Regular.ttf(サイトの見出しと同じ。OFL)、
本文は Windows 標準の BIZ UDゴシック Bold(サイト本文の BIZ UDPGothic と同じ系統)。
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "og-image.png"
DISPLAY = str(ROOT / "tools" / "fonts" / "DelaGothicOne-Regular.ttf")
BODY = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"

S = 2  # 2倍で描いて縮小し、斜めの線をなめらかにする
W, H = 1200 * S, 630 * S
INK = (21, 23, 43)
PAPER = (242, 243, 247)
ONAIR = (232, 25, 90)
MARKER = (255, 225, 74)


def font(path, size):
    return ImageFont.truetype(path, size * S)


base = Image.new("RGB", (W, H), INK)
draw = ImageDraw.Draw(base, "RGBA")

# ---- 網点(焦点から離れるほど濃い)
fx, fy = W * 0.80, H * 0.40
step = 9 * S
for y in range(0, H, step):
    for x in range(0, W, step):
        d = math.hypot(x - fx, y - fy) / math.hypot(W, H)
        if d > 0.16:
            a = int(min(1, (d - 0.16) / 0.45) * 46)
            r = 1.5 * S
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(*PAPER, a))

# ---- 集中線(ところどころピンク)
random.seed(11)
R = math.hypot(W, H)
for i in range(190):
    ang = i / 190 * math.tau + random.random() * 0.025
    width = 0.003 + random.random() * 0.011
    inner = (190 + random.random() * 160) * S
    color = (*ONAIR, 120) if random.random() < 0.08 else (*PAPER, 62)
    draw.polygon(
        [
            (fx + math.cos(ang - width) * R, fy + math.sin(ang - width) * R),
            (fx + math.cos(ang) * inner, fy + math.sin(ang) * inner),
            (fx + math.cos(ang + width) * R, fy + math.sin(ang + width) * R),
        ],
        fill=color,
    )

# ---- サイト名。「全部」は効果音の描き文字のように大きく傾けて、ピンクの版ずれ影を付ける
x0 = 70 * S
draw.text((x0, 70 * S), "アニメニュース", font=font(DISPLAY, 92), fill=PAPER)

sfx_font = font(DISPLAY, 250)
sfx = Image.new("RGBA", (720 * S, 360 * S), (0, 0, 0, 0))
sd = ImageDraw.Draw(sfx)
ox, oy = 30 * S, 10 * S
sd.text((ox + 12 * S, oy + 12 * S), "全部", font=sfx_font, fill=ONAIR)
sd.text((ox, oy), "全部", font=sfx_font, fill=PAPER, stroke_width=6 * S, stroke_fill=INK)
sfx = sfx.rotate(5, resample=Image.BICUBIC, expand=True)
base.paste(sfx, (x0 - 44 * S, 150 * S), sfx)

# ---- フキダシ3つ(機能)
body = font(BODY, 30)
bubbles = [
    ("21媒体を1時間ごとに収集", (742, 92), -3),
    ("転載・重複はひとつに", (786, 230), 2),
    ("推し作品だけに絞れる", (748, 366), -2),
]
for text, (bx, by), rot in bubbles:
    tw = draw.textlength(text, font=body)
    pad_x, pad_y = 30 * S, 24 * S
    bw, bh = int(tw + pad_x * 2), int(30 * S + pad_y * 2)
    layer = Image.new("RGBA", (bw + 40 * S, bh + 50 * S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((8 * S, 8 * S, bw + 8 * S, bh + 8 * S), 40 * S, fill=ONAIR)
    ld.rounded_rectangle((0, 0, bw, bh), 40 * S, fill=PAPER)
    ld.polygon([(36 * S, bh - 2 * S), (70 * S, bh - 2 * S), (40 * S, bh + 30 * S)], fill=PAPER)
    ld.text((pad_x, pad_y - 2 * S), text, font=body, fill=INK)
    layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    base.paste(layer, (bx * S, by * S), layer)

# ---- 下の速報帯
band_h = 64 * S
draw.rectangle((0, H - band_h, W, H), fill=(11, 12, 26))
draw.rectangle((0, H - band_h, W, H - band_h + 3 * S), fill=ONAIR)
draw.rectangle((0, H - band_h + 3 * S, 128 * S, H), fill=ONAIR)
draw.text((30 * S, H - band_h + 13 * S), "速報", font=font(DISPLAY, 30), fill=(255, 255, 255))
draw.text(
    (156 * S, H - band_h + 16 * S),
    "新作・放送・PV・キャスト・グッズ",
    font=font(BODY, 26),
    fill=PAPER,
)
url_font = font(BODY, 22)
url = "fourgetkun.com/anime-news"
draw.text((W - 40 * S - draw.textlength(url, font=url_font), H - band_h + 20 * S), url, font=url_font, fill=MARKER)

img = base.resize((1200, 630), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1, percent=40, threshold=2))
OUT.parent.mkdir(parents=True, exist_ok=True)
# 網点で色数が多く PNG が重くなる(約540KB)ので、256色に減色する(見た目はほぼ変わらない)
img = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
img.save(OUT, optimize=True)
print(OUT, OUT.stat().st_size)
