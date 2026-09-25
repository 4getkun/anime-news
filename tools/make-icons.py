"""ファビコン一式を作る。

図柄: インクの角丸四角に、サイト名の「全」を1文字。OG画像の「全部」と同じく、
マンガの効果音(描き文字)のように少し傾け、ピンクの版ずれ影を付ける。
(以前の「白いフキダシ＋ピンクの点＋周りの線」は、めざましテレビのロゴに見えるので
 やめた。丸・点・放射線の組み合わせは避けること)

SVG は Dela Gothic One の「全」の輪郭をパスとして埋め込むので、閲覧側にフォントは要らない。
PNG/ICO は同じフォントを Pillow で描く。要 Pillow・fontTools。
    python tools/make-icons.py

出力(public/):
  favicon.svg           … ふつうのブラウザ用・ヘッダーのロゴ
  favicon.ico           … 16/32/48px(SVG 非対応の環境・検索結果用)
  apple-touch-icon.png  … 180px(iOS のホーム画面)
  icon-192.png / icon-512.png … Android・PWA 用
"""
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"
FONT = ROOT / "tools" / "fonts" / "DelaGothicOne-Regular.ttf"
CHAR = "全"
INK = "#15172B"
PAPER = "#F2F3F7"
ONAIR = "#E8195A"

# 64x64 基準
RADIUS = 14
GLYPH_BOX = 44  # 文字の外接矩形の長辺をこの大きさにする
ROTATE = -6  # 度(反時計回り)。描き文字らしく少し傾ける
SHADOW = 3.2  # 版ずれ影のずれ(右下)


def glyph_path() -> str:
    """「全」の輪郭を、64x64 の中央に GLYPH_BOX の大きさで置いた SVG パスにする"""
    font = TTFont(FONT)
    gs = font.getGlyphSet()
    glyph = gs[font.getBestCmap()[ord(CHAR)]]
    bp = BoundsPen(gs)
    glyph.draw(bp)
    x0, y0, x1, y1 = bp.bounds
    k = GLYPH_BOX / max(x1 - x0, y1 - y0)
    # フォントは y が上向きなので反転し、中央へ寄せる
    dx = 32 - (x0 + x1) / 2 * k
    dy = 32 + (y0 + y1) / 2 * k
    sp = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    glyph.draw(TransformPen(sp, (k, 0, 0, -k, dx, dy)))
    return sp.getCommands()


def svg() -> str:
    d = glyph_path()
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="{RADIUS}" fill="{INK}"/>'
        f'<g transform="rotate({ROTATE} 32 32)">'
        f'<path d="{d}" fill="{ONAIR}" transform="translate({SHADOW} {SHADOW})"/>'
        f'<path d="{d}" fill="{PAPER}"/>'
        "</g></svg>\n"
    )


def png(size: int, rotate: bool = True, rounded: bool = True) -> Image.Image:
    ss = 8  # 8倍で描いて縮小
    big = size * ss
    k = big / 64
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle((0, 0, big - 1, big - 1), RADIUS * k, fill=INK)
    else:
        d.rectangle((0, 0, big, big), fill=INK)

    # 文字は別の層に描いて中央に置き、傾けてから重ねる
    font = ImageFont.truetype(str(FONT), int(GLYPH_BOX * k * 1.2))
    l, t, r, b = font.getbbox(CHAR)
    scale = GLYPH_BOX * k / max(r - l, b - t)
    font = ImageFont.truetype(str(FONT), int(GLYPH_BOX * k * 1.2 * scale))
    l, t, r, b = font.getbbox(CHAR)
    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ox = big / 2 - (l + r) / 2
    oy = big / 2 - (t + b) / 2
    # 16px では影を1pxに収める(ずれが大きいと文字が太って潰れる)
    shadow = SHADOW * k if size > 16 else ss
    ld.text((ox + shadow, oy + shadow), CHAR, font=font, fill=ONAIR)
    ld.text((ox, oy), CHAR, font=font, fill=PAPER)
    if rotate:
        layer = layer.rotate(-ROTATE, resample=Image.BICUBIC)
    img.alpha_composite(layer)
    return img.resize((size, size), Image.LANCZOS)


(OUT / "favicon.svg").write_text(svg(), encoding="utf-8")
# Pillow は基準画像より大きいサイズを書かないので、48px を基準にして 16/32px を添える。
# 16px は傾けるとにじむので、まっすぐにする
png(48).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[png(16, rotate=False), png(32)])
# iOS は自分で角を丸めるので、四角いまま塗りつぶす
png(180, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
png(192).save(OUT / "icon-192.png", optimize=True)
png(512).save(OUT / "icon-512.png", optimize=True)
for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
    print(name, (OUT / name).stat().st_size)
