// node --test scripts/ で実行される、収集時フィルタの単体テスト
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  containsKeyword,
  evaluateItem,
  extractWorks,
  canonicalWork,
  splitPublisherSuffix,
  dedupeItems,
  isSpoiler,
  isSyndicated,
  originalPublisherFromTitle,
  classifyCategories,
  workKey,
  buildWorkDisplayMap,
} from "./filter.mjs";

const config = JSON.parse(readFileSync(new URL("../../src/data/filters.json", import.meta.url), "utf-8"));
const specialist = { id: "s", kind: "specialist", lang: "ja" };
const general = { id: "g", kind: "general", lang: "ja" };
const press = { id: "p", kind: "press", lang: "ja" };

test("英単語キーワードは単語境界で判定する", () => {
  assert.equal(containsKeyword("New event announced", "event"), true);
  assert.equal(containsKeyword("How to prevent burnout", "event"), false);
  assert.equal(containsKeyword("ＰＶ公開", "PV"), true); // 全角も半角に寄せて判定
});

test("広告・成人向けはどのフィードでも除外", () => {
  assert.equal(evaluateItem({ title: "【PR】TVアニメ『X』コラボ", summary: "" }, specialist, config), null);
  assert.equal(evaluateItem({ title: "アニメ『X』R18版", summary: "" }, specialist, config), null);
});

test("専門媒体はスコアに関係なく採用、総合媒体はしきい値で判定", () => {
  assert.ok(evaluateItem({ title: "「X」スタンプ登場", summary: "" }, specialist, config));
  assert.equal(evaluateItem({ title: "iPhone 18 Proを分解", summary: "" }, general, config), null);
  assert.ok(evaluateItem({ title: "TVアニメ『X』2027年1月放送決定", summary: "" }, general, config));
  // 実写ドラマの主題歌ニュースは総合媒体からは拾わない
  assert.equal(evaluateItem({ title: "新曲が主演ドラマの主題歌に", summary: "" }, general, config), null);
});

test("作品辞書に載っている作品名は、アニメという語が無くても加点される", () => {
  const item = { title: "『ちいかわ』マスコット全4種が受注生産決定", summary: "" };
  assert.equal(evaluateItem(item, general, config), null);
  assert.ok(evaluateItem(item, general, config, new Set([workKey("ちいかわ", config)])));
  // プレスリリースは作品名だけでは足りない(PR TIMES は量が多く雑多なため)
  assert.equal(evaluateItem(item, press, config, new Set([workKey("ちいかわ", config)])), null);
});

test("feeds.json の minScore はフィード種別のしきい値より優先", () => {
  const item = { title: "誕生祭のバースデーカード配布", summary: "アニメ放送記念" };
  assert.equal(evaluateItem(item, general, config), null);
  assert.ok(evaluateItem(item, { ...general, minScore: 2 }, config));
});

test("作品名の抽出と正規化", () => {
  assert.deepEqual(extractWorks("TVアニメ『薬屋のひとりごと』第3期、PV公開", config), ["薬屋のひとりごと"]);
  assert.deepEqual(extractWorks("アニメ「ちいかわ」新作を休止", config), ["ちいかわ"]);
  // 発言の引用っぽい「」は、専門媒体の寛容モードでも拾わない
  assert.deepEqual(extractWorks("声優が語る「本当に楽しかった！」", config, { lenient: true }), []);
  assert.equal(canonicalWork("劇場版 メダリスト", config), "メダリスト");
  assert.equal(canonicalWork("無職転生 Season 2", config), "無職転生");
});

test("Googleニュースの「見出し - 媒体名」を分離", () => {
  assert.deepEqual(splitPublisherSuffix("アニメ『X』放送決定 - コミックナタリー"), {
    title: "アニメ『X』放送決定",
    publisher: "コミックナタリー",
  });
});

test("ネタバレ判定", () => {
  assert.equal(isSpoiler("『X』第12話 衝撃の展開", config), true);
  assert.equal(isSpoiler("『X』PV公開", config), false);
});

test("同一ニュースは統合し、別ニュースは統合しない", () => {
  const base = { summary: "", image: null, categories: [], spoiler: false, score: 0, lang: "ja" };
  const items = [
    { ...base, title: "アニメ「新 美味しんぼ」メインキャストに阿座上洋平、咲々木瞳、大塚明夫", link: "https://a/1", pubDate: "2026-09-24T10:00:00Z", works: ["新 美味しんぼ"], sources: [{ name: "A", sourceId: "a", link: "https://a/1" }] },
    { ...base, title: "アニメ「新 美味しんぼ」メインキャストに阿座上洋平、咲々木瞳、大塚明夫 - B", link: "https://b/1", pubDate: "2026-09-24T11:00:00Z", works: ["新 美味しんぼ"], sources: [{ name: "B", sourceId: "b", link: "https://b/1" }] },
    { ...base, title: "『呪術廻戦』スタンプ登場", link: "https://c/1", pubDate: "2026-09-24T10:30:00Z", works: ["呪術廻戦"], sources: [{ name: "C", sourceId: "c", link: "https://c/1" }] },
  ];
  const out = dedupeItems(items);
  assert.equal(out.length, 2);
  const merged = out.find((it) => it.sources.length === 2);
  assert.ok(merged);
  assert.equal(merged.pubDate, "2026-09-24T10:00:00.000Z"); // 一番早い報道時刻を採用
});

const mk = (title, link, pubDate, extra = {}) => ({
  title, link, pubDate, summary: "", image: null, categories: [], spoiler: false, score: 0, lang: "ja", works: [],
  sources: [{ name: extra.source ?? link, sourceId: "x", link, ...(extra.syndicated ? { syndicated: true } : {}) }],
  ...extra,
});

test("再配信ポータルの判定", () => {
  assert.equal(isSyndicated({ source: "Yahoo!ニュース", link: "https://news.google.com/x" }, config), true);
  assert.equal(isSyndicated({ source: "オリコン", link: "https://news.yahoo.co.jp/articles/abc" }, config), true);
  assert.equal(isSyndicated({ source: "コミックナタリー", link: "https://natalie.mu/comic/news/1" }, config), false);
  assert.equal(originalPublisherFromTitle("声優が被害届(日刊スポーツ)"), "日刊スポーツ");
});

test("再配信は数日遅れでも元記事にまとまり、代表は元記事になる", () => {
  const out = dedupeItems([
    mk("アニメ「ちいかわ」新作放送を一時休止しリバイバル放送へ", "https://natalie.mu/1", "2026-09-22T10:00:00Z", { source: "コミックナタリー" }),
    mk("アニメ「ちいかわ」新作放送を一時休止し、リバイバル放送へ(コミックナタリー)", "https://news.yahoo.co.jp/a", "2026-09-24T09:00:00Z", { source: "Yahoo!ニュース", syndicated: true }),
  ]);
  assert.equal(out.length, 1);
  assert.equal(out[0].source, "コミックナタリー");
  assert.equal(out[0].syndicated, false);
});

test("同じ作品の別の話題はまとめない", () => {
  const w = { works: ["薬屋のひとりごと"] };
  const out = dedupeItems([
    mk("TVアニメ『薬屋のひとりごと』第3期、本PV公開", "https://a/1", "2026-09-24T10:00:00Z", w),
    mk("TVアニメ『薬屋のひとりごと』一番くじ発売決定", "https://b/1", "2026-09-24T11:00:00Z", w),
  ]);
  assert.equal(out.length, 2);
});

test("似た見出しの連鎖で無関係な記事がまとまらない", () => {
  const out = dedupeItems([
    // A≒B(0.55)、B≒C(0.60) だが A と C は似ていない(0.29)
    mk("あいうえおかきくけこさしすせそた", "https://a/1", "2026-09-24T10:00:00Z"),
    mk("おかきくけこさしすせそたちつてとな", "https://b/1", "2026-09-24T10:30:00Z"),
    mk("けこさしすせそたちつてとなにぬねの", "https://c/1", "2026-09-24T11:00:00Z"),
  ]);
  assert.equal(out.length, 2);
});

test("映画と書かれていない映画の記事も映画枠に入る", () => {
  const t = "「アベンジャーズ　エンドゲーム：アンコール」公開記念イベントに米倉涼子、内田有紀、加藤浩次、遠藤憲一ら日本版声優陣が登場";
  const cats = classifyCategories(t, "", config);
  assert.ok(cats.includes("movie"));
  assert.ok(!cats.includes("game")); // 「エンドゲーム」はゲームではない
  assert.ok(classifyCategories("『X』入場者特典第3弾が決定", "", config).includes("movie"));
  assert.ok(!classifyCategories("TVアニメ『X』第2弾PV公開", "", config).includes("movie"));
});

test("見たくない話題(事件・熱愛・訃報)は見出しだけで、作品名やあらすじは無視して判定", () => {
  const has = (t, id, sum = "") => classifyCategories(t, sum, config).includes(id);
  assert.ok(has("声優・上坂すみれ、脅迫行為に関する対応発表 被害届を提出", "trouble"));
  assert.ok(has("人気声優の○○が一般女性と結婚を発表", "romance"));
  assert.ok(!has("TVアニメ『わたしの幸せな結婚』第2期PV公開", "romance")); // 作品名
  assert.ok(!has("『名探偵コナン』最新話", "trouble", "殺害予告を受けた依頼人…")); // あらすじ
  assert.ok(!has("『X』第5話先行カット", "obituary", "母の死去をきっかけに…"));
});

test("作品名の表記ゆれは同じキー・同じ表示名になる", () => {
  assert.equal(workKey("リゼロ", config), workKey("Re:ゼロから始める異世界生活", config));
  assert.equal(workKey("転スラ", config), workKey("転生したらスライムだった件", config));
  assert.equal(workKey("【推しの子】", config), workKey("推しの子", config));
  const madoka = ["まどマギ〈ワルプルギスの廻天〉", "魔法少女まどか☆マギカ〈ワルプルギスの廻天〉", "まどマギ〈廻天〉"];
  assert.equal(new Set(madoka.map((w) => workKey(w, config))).size, 1);
  // 別の作品は別のキー(シリーズと劇場版、無印と「新」)
  assert.notEqual(workKey("まどか☆マギカ", config), workKey("まどマギ〈廻天〉", config));
  assert.notEqual(workKey("美味しんぼ", config), workKey("新 美味しんぼ", config));
  const map = buildWorkDisplayMap(["リゼロ", "リゼロ", "Re:ゼロから始める異世界生活"], config);
  assert.equal(map.get("Re:ゼロから始める異世界生活"), "リゼロ"); // 一番多い表記
});

test("予定の抽出: 日付＋動詞を拾い、年を補う", async () => {
  const { extractSchedules } = await import("./filter.mjs");
  const pub = "2026-09-25T03:00:00Z"; // JST 9/25
  const ex = (t) => extractSchedules(t, pub, config).map((e) => `${e.date}:${e.verb}`);
  assert.deepEqual(ex("TVアニメ『X』10月3日より放送開始"), ["2026-10-03:broadcast"]);
  assert.deepEqual(ex("劇場版『X』2027年2月19日公開決定"), ["2027-02-19:movie"]);
  assert.deepEqual(ex("『X』Blu-ray 12/10発売"), ["2026-12-10:release"]);
  assert.deepEqual(ex("『X』2027年1月から配信"), ["2027-01:stream"]);
  assert.deepEqual(ex("『X』1月8日放送"), ["2027-01-08:broadcast"]); // 年が無く過去なら翌年
  assert.deepEqual(ex("『X』コミックス本日発売"), ["2026-09-25:release"]);
  assert.deepEqual(ex("『X』予約受付は10月5日まで"), []); // 締め切り
  assert.deepEqual(ex("『X』12月10日にPV公開"), []); // PVの公開は予定ではない
  assert.deepEqual(ex("『X』9月20日に聖地を訪問"), []); // 動詞が無い
});

test("予定の抽出: 毎週の話数告知と「本日限定」は拾わない", async () => {
  const { extractSchedules } = await import("./filter.mjs");
  const pub = "2026-09-25T03:00:00Z";
  assert.deepEqual(extractSchedules("9月25日(金)放送 TVアニメ『X』第96話あらすじ", pub, config), []);
  assert.deepEqual(extractSchedules("「LINEマンガ」で本日限定の記念ミッションを開催", pub, config), []);
});

test("予定の抽出: 過去形の出来事は拾わず、少し前の日付を来年にしない", async () => {
  const { extractSchedules } = await import("./filter.mjs");
  const pub = "2026-09-25T03:00:00Z";
  const ex = (t) => extractSchedules(t, pub, config).map((e) => `${e.date}:${e.verb}`);
  assert.deepEqual(ex("7月15日には新シリーズが放送され、7月24日には映画が公開された"), []);
  assert.deepEqual(ex("『X』8月1日に発売した新刊が重版"), []);
  assert.deepEqual(ex("『X』1月8日放送開始"), ["2027-01-08:broadcast"]); // 150日以上前なら来年
  assert.deepEqual(ex("『X』7月15日放送"), ["2026-07-15:broadcast"]); // 72日前なら今年のまま
});
