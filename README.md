# アニメニュース全部

アニメ関連ニュースのRSSを片っ端から集め、関係ない記事・転載・重複を落として、読みたいものだけに絞り込めるようにした静的サイトです。
[Curation_NPB](https://github.com/4getkun/Curation_NPB) と同じく、Astro + GitHub Actions + GitHub Pages の無料枠だけで動きます。

- 公開URL（Pages有効化後）: https://4getkun.github.io/anime-news/
- 更新: GitHub Actions が30分ごとにRSSを取得 → コミット → ビルド → 公開

## しくみ

```
feeds.json の21媒体 ─┐
                    ├─ scripts/fetch-news.mjs
                    │    1. 取得して data/archive.json に30日分を積み増し（生データ）
                    │    2. アーカイブ全体に filters.json のルールをかけ直す
                    │    3. 再配信・重複をまとめて src/data/news.json に書き出し
                    └─ Astro がビルド。/data/news.json をブラウザ側の絞り込みUIが読む
```

生データと表示用データを分けているので、`filters.json` を変えると次の更新で過去30日分にもそのまま効きます。

### 収集時フィルタ（`scripts/lib/filter.mjs` / `src/data/filters.json`）

| 段階 | 内容 |
| --- | --- |
| 除外 | 広告・PR、成人向け、求人などは無条件で捨てる |
| 関連度スコア | 語ごとの重み（見出しは2倍、「アニメ調」「主演ドラマ」などは減点）の合計を、媒体の種類ごとのしきい値と比べる。専門媒体は全部採用、総合4点・プレス5点・Googleニュース2点。`feeds.json` の `minScore` で媒体ごとに上書きできる |
| 作品辞書 | 専門媒体の見出しの『』から作品名を集め、総合媒体の見出しにその作品名があれば加点する |
| カテゴリ | 新作・放送・PV・キャスト・劇場版・音楽・イベント・グッズ…の14種を複数付与 |
| ネタバレ | 「最終回」「第◯話」などに印を付け、表示時にぼかす |
| 再配信の統合 | Yahoo!ニュース・dメニュー・エキサイト等（`filters.json` の `syndication`）の記事は、見出しの完全一致か、72時間以内で類似度0.7以上なら元記事にまとめる。元記事が無ければ「元媒体名（ポータル名）」として残す |
| 同じ話題の統合 | 12時間以内・見出しの2文字Jaccard 0.55以上。同じ作品同士は作品名を除いて比べる。グループの最初の記事とも似ていることを条件にして、似た記事の数珠つなぎを防ぐ |

統合のうち「作品名を除いて比べる」と「最初の記事との類似を条件にする」は、news-lifespan のクラスタリングの考え方（ありふれた語だけの一致を無視する・union-find の連鎖を防ぐ）を移植したものです。
形態素解析（fugashi + unidic）によるトークン化とSQLiteでのストーリー追跡は、Nodeだけで動かす構成に合わず、アニメでは『』の作品名がその役割をほぼ果たすため取り入れていません。

### 表示時フィルタ（`src/scripts/feed.ts`）

- 初期表示は日本語の記事のみ（英語は「すべて」「English」で表示）
- キーワード（スペースでAND、`-語` で除外、`/` キーで検索欄へ）、カテゴリ、期間、話題順
- 作品フォロー、ミュートワード、媒体の表示切り替え、既読の薄表示・非表示、ネタバレぼかし
- 条件はURLに、好みはブラウザの localStorage に保存

## 開発

```bash
npm install
npm run fetch-news   # RSSを取得して data/ と src/data/news.json を更新
npm run dev          # http://localhost:4321/anime-news/
npm test             # フィルタの単体テスト
npm run probe-feeds  # feeds.json の全フィードの生存確認（URLを渡すとそのURLだけ）
```

媒体を追加するときは `npm run probe-feeds <URL>` で取れることを確かめてから `src/data/feeds.json` に足します。
`kind` は `specialist`（アニメ専門）/ `general`（総合・ゲーム）/ `aggregator`（Googleニュース検索）/ `press`（プレスリリース）のどれかです。

## GitHub Pages の設定

1. Settings → Pages → Source を **GitHub Actions** にする
2. Settings → Actions → General → Workflow permissions を **Read and write** にする
3. Actions タブで「Update news and deploy to GitHub Pages」を手動実行（以後は30分ごとに自動）

## 著作権について

記事本文はコピーしていません。見出し・短い要約・RSSが配信しているサムネイルURL・リンクのみを掲載し、全文は配信元へ誘導します。
