// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// 公開URL: https://fourgetkun.com/anime-news/ (fourgetkun-hub 配下)
//
// ビルド成果物は Cloudflare Pages のプロジェクト anime-news (https://anime-news-a7f.pages.dev) へ
// GitHub Actions から Direct Upload する。ここは「配信元」で、利用者が見るのは
// fourgetkun.com/anime-news/。fourgetkun-hub の Worker(src/pages-proxy/proxy.js)が
// /anime-news/* を pages.dev から取ってきて返す(news-lifespan と同じ方式。リポジトリを private のままにできる)。
// そのため site/base は公開側に合わせる。pages.dev を直接開かれたら Base.astro が公開側へ転送する。
//
// 静的出力のみ(アダプターは使わない)。2026-09 時点の wrangler は `pages project create` を
// Workers へ振り替え、このプロジェクトを Workers + @astrojs/cloudflare に書き換えようとする。
// Pages プロジェクトは `--force` 付きで一度だけ作成済み(名前は anime-news、ドメインは
// anime-news-a7f.pages.dev)。以後の `wrangler pages deploy` はそのまま Pages へ届く。
export default defineConfig({
  site: 'https://fourgetkun.com',
  base: '/anime-news',
  trailingSlash: 'always',
  // CSS は HTML に埋め込む(別ファイルだと描画を止めるリクエストが1つ増える)
  build: { inlineStylesheets: 'always' },
  vite: {
    plugins: [tailwindcss()],
  },
});
