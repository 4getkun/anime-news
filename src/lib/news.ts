import newsData from "../data/news.json";
import feedsData from "../data/feeds.json";
import filtersData from "../data/filters.json";

export type FeedKind = "specialist" | "general" | "aggregator" | "press";

export interface NewsSource {
  name: string;
  sourceId: string;
  link: string;
  via?: string;
  /** Yahoo!ニュース等の再配信ポータル経由 */
  syndicated?: boolean;
}

export interface NewsItem {
  title: string;
  summary: string;
  link: string;
  pubDate: string | null;
  image: string | null;
  source: string;
  sourceId: string;
  kind: FeedKind;
  lang: "ja" | "en";
  score: number;
  categories: string[];
  works: string[];
  spoiler: boolean;
  /** 元記事が見つからず、再配信ポータルの記事だけが残っているもの */
  syndicated?: boolean;
  sources: NewsSource[];
}

export interface FeedStatus {
  id: string;
  name: string;
  kind: FeedKind;
  lang: string;
  ok: boolean;
  error: string | null;
  fetched: number;
  archived: number;
  accepted: number;
}

export interface Category {
  id: string;
  label: string;
  emoji: string;
  keywords: string[];
}

const data = newsData as unknown as {
  generatedAt: string;
  count: number;
  dedupe?: { exact: number; syndicated: number; similar: number; syndicatedTotal: number; syndicatedLeft: number };
  feeds: FeedStatus[];
  items: NewsItem[];
};

export const allNews = data.items;
/** 初期表示と同じく日本語の記事だけ(ヒーロー・テロップ・JS無効時の一覧用) */
export const jaNews = allNews.filter((it) => it.lang === "ja");
export const generatedAt = data.generatedAt;
export const feedStatus = data.feeds;
export const dedupeStats = data.dedupe;
export const feeds = feedsData as { id: string; name: string; url: string; kind: FeedKind; lang: string; minScore?: number }[];
export const categories = (filtersData as unknown as { categories: Category[] }).categories;
export const thresholds = (filtersData as unknown as { thresholds: Record<FeedKind, number> }).thresholds;

export const kindLabels: Record<FeedKind, string> = {
  specialist: "アニメ専門媒体",
  general: "総合・ゲーム媒体",
  aggregator: "Googleニュース経由",
  press: "プレスリリース",
};

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return new Intl.DateTimeFormat("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Tokyo",
  }).format(d);
}

/** 直近 hours 時間に報じられた件数が多い作品(ヒーローと作品ランキング用) */
export function trendingWorks(hours = 72, limit = 12): { name: string; count: number }[] {
  const base = new Date(generatedAt).getTime() || Date.now();
  const cutoff = base - hours * 3600_000;
  const counts = new Map<string, number>();
  for (const item of jaNews) {
    const t = item.pubDate ? Date.parse(item.pubDate) : NaN;
    if (Number.isNaN(t) || t < cutoff) continue;
    for (const w of item.works) counts.set(w, (counts.get(w) ?? 0) + item.sources.length);
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}
