"""見出し用フォント(Dela Gothic One)を、サイトで使う文字だけに絞った woff2 にする。

    python tools/make-font-subset.py

- Google Fonts から読むと、日本語フォントは約120個の小さなファイルに分かれていて、
  届くたびにページ全体の文字の配置をやり直すため、トップの最初の表示が遅くなっていた
  (Lighthouse のスマホ条件で最初の表示 3.1秒 → 自前の絞ったフォントで 1秒台)。
- 対象の文字: src/ のテンプレート・スクリプト・設定に書かれた文字 + ASCII + かな + 日付の表示に使う文字。
  作品名のように毎時変わる文字は含めない(作品名を出す見出しは本文の書体にしている)。
- テンプレートの文言を変えたら実行し直して public/fonts/ をコミットする。
  必要なもの: pip install fonttools brotli
"""
import glob
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "fonts" / "DelaGothicOne-Regular.ttf"
OUT = ROOT / "public" / "fonts" / "dela-gothic-one-sub.woff2"

chars = set()
for pattern in ("src/**/*.astro", "src/**/*.ts", "src/data/filters.json"):
    for f in glob.glob(str(ROOT / pattern), recursive=True):
        chars |= set(Path(f).read_text(encoding="utf-8"))
chars |= {chr(c) for c in range(0x20, 0x7F)}  # ASCII
chars |= {chr(c) for c in range(0x3040, 0x3100)}  # ひらがな・カタカナ
chars |= set("０１２３４５６７８９、。！？・ー「」『』（）〜…年月日今昨曜火水木金土")
text = "".join(sorted(c for c in chars if c.strip()))

tmp = ROOT / "tools" / ".subset-chars.txt"
tmp.write_text(text, encoding="utf-8")
try:
    subprocess.run(
        [sys.executable, "-m", "fontTools.subset", str(SRC), f"--text-file={tmp}", "--flavor=woff2", f"--output-file={OUT}"],
        check=True,
    )
finally:
    tmp.unlink(missing_ok=True)
print(f"{OUT.relative_to(ROOT)}: {len(text)} chars, {OUT.stat().st_size // 1024} KB")
