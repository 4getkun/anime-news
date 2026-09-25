"""ファビコン一式を作る。

図柄はインクの角丸四角にサイト名の「全」1文字。大きさで2種類に描き分ける。

- 小さいもの(favicon.svg・favicon.ico・ヘッダーのロゴ): BIZ UDゴシック Bold の「全」を
  四角いっぱいに、まっすぐ置くだけ。ブラウザのタブ(16px)では、極太の Dela Gothic や
  傾き・影があると「王」の横線がつぶれて読めなかった。UD書体は小さくても線の間が残る。
  ICO の 16/32/48px は縮小ではなく、その大きさでフォントのヒンティングを効かせて描く。
- 大きいもの(apple-touch-icon・icon-192/512): OG画像と同じく Dela Gothic One の「全」を
  描き文字のように傾け、ピンクの版ずれ影を付ける。

(以前の「白いフキダシ＋ピンクの点＋周りの線」は、めざましテレビのロゴに見えるので
 やめた。丸・点・放射線の組み合わせは避けること)

SVG は「全」の輪郭をパスとして埋め込むので、閲覧側にフォントは要らない。
フォントは tools/fonts/ に置いた OFL のもの。要 Pillow・fontTools。
    python tools/make-icons.py
"""
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"
FONTS = ROOT / "tools" / "fonts"
SMALL_FONT = FONTS / "BIZUDGothic-Bold.ttf"
LARGE_FONT = FONTS / "DelaGothicOne-Regular.ttf"
CHAR = "全"
INK = "#15172B"
PAPER = "#F2F3F7"
ONAIR = "#E8195A"

# 64x64 基準
SMALL_RADIUS = 12
SMALL_GLYPH = 56  # タブで読めるよう、ほぼいっぱいに
LARGE_RADIUS = 14
LARGE_GLYPH = 44
LARGE_ROTATE = -6  # 度(反時計回り)
LARGE_SHADOW = 3.2


def glyph_path(font_path: Path, box: float) -> str:
    """「全」の輪郭を、64x64 の中央に box の大きさで置いた SVG パスにする"""
    font = TTFont(font_path)
    gs = font.getGlyphSet()
    glyph = gs[font.getBestCmap()[ord(CHAR)]]
    bp = BoundsPen(gs)
    glyph.draw(bp)
    x0, y0, x1, y1 = bp.bounds
    k = box / max(x1 - x0, y1 - y0)
    # フォントは y が上向きなので反転し、中央へ寄せる
    dx = 32 - (x0 + x1) / 2 * k
    dy = 32 + (y0 + y1) / 2 * k
    sp = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    glyph.draw(TransformPen(sp, (k, 0, 0, -k, dx, dy)))
    return sp.getCommands()


def small_svg() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="{SMALL_RADIUS}" fill="{INK}"/>'
        f'<path d="{glyph_path(SMALL_FONT, SMALL_GLYPH)}" fill="{PAPER}"/>'
        "</svg>\n"
    )


def centered_font(font_path: Path, target: float) -> tuple[ImageFont.FreeTypeFont, tuple[float, float, float, float]]:
    """文字の外接矩形の長辺が target px になる大きさのフォントを返す"""
    size = max(1, round(target))
    for _ in range(4):
        font = ImageFont.truetype(str(font_path), size)
        l, t, r, b = font.getbbox(CHAR)
        size = max(1, round(size * target / max(r - l, b - t)))
    font = ImageFont.truetype(str(font_path), size)
    return font, font.getbbox(CHAR)


def small_png(size: int) -> Image.Image:
    """タブ用。縮小せず、その大きさで直接描く(ヒンティングで線がピクセルに揃う)"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size - 1, size - 1), SMALL_RADIUS * size / 64, fill=INK)
    font, (l, t, r, b) = centered_font(SMALL_FONT, size * SMALL_GLYPH / 64)
    d.text((round((size - (r - l)) / 2 - l), round((size - (b - t)) / 2 - t)), CHAR, font=font, fill=PAPER)
    return img


def large_png(size: int, rounded: bool = True) -> Image.Image:
    ss = 4  # 4倍で描いて縮小
    big = size * ss
    k = big / 64
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle((0, 0, big - 1, big - 1), LARGE_RADIUS * k, fill=INK)
    else:
        d.rectangle((0, 0, big, big), fill=INK)
    font, (l, t, r, b) = centered_font(LARGE_FONT, LARGE_GLYPH * k)
    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ox, oy = big / 2 - (l + r) / 2, big / 2 - (t + b) / 2
    ld.text((ox + LARGE_SHADOW * k, oy + LARGE_SHADOW * k), CHAR, font=font, fill=ONAIR)
    ld.text((ox, oy), CHAR, font=font, fill=PAPER)
    img.alpha_composite(layer.rotate(-LARGE_ROTATE, resample=Image.BICUBIC))
    return img.resize((size, size), Image.LANCZOS)


(OUT / "favicon.svg").write_text(small_svg(), encoding="utf-8")
# Pillow は基準画像より大きいサイズを書かないので、48px を基準にして 16/32px を添える
small_png(48).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[small_png(16), small_png(32)])
# iOS は自分で角を丸めるので、四角いまま塗りつぶす
large_png(180, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
large_png(192).save(OUT / "icon-192.png", optimize=True)
large_png(512).save(OUT / "icon-512.png", optimize=True)
for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
    print(name, (OUT / name).stat().st_size)
