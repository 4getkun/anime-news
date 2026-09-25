// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// 公開URL: https://4getkun.github.io/anime-news/ (GitHub Pages)
// 独自ドメイン配下(fourgetkun.com/anime-news/ 等)へ移す場合は Curation_NPB と同じく
// site/base をそちらに合わせる。
export default defineConfig({
  site: 'https://4getkun.github.io',
  base: '/anime-news',
  trailingSlash: 'always',
  vite: {
    plugins: [tailwindcss()],
  },
});
