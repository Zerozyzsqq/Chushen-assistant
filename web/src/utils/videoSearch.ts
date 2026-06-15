/** Build third-party video search URLs (Bilibili / Douyin). No API keys required. */

const SEARCH_SUFFIX = "教程";

export type VideoPlatform = "bilibili" | "douyin";

const GENERIC_TITLES = new Set(["这道菜", "菜谱详情", "菜谱推荐", "本周菜单", "今日午餐", "今日晚餐"]);

/** Strip noise from vision/LLM text so search uses clean dish names. */
export function sanitizeDishName(raw: string): string {
  let name = (raw || "").trim().replace(/\*\*/g, "");
  name = name.replace(/[\u{1F300}-\u{1FAFF}]/gu, "");
  name = name.replace(/^(看到|识别|分享|这是|您的|您分享的?|已经?)+/u, "");
  name = name.replace(/(图片了?|的照片?|成品图?|的样子?|教程|做法|分享)$/u, "");
  if (name.length > 4 && /[了了的]$/u.test(name)) {
    name = name.slice(0, -1);
  }
  name = name.replace(/图片了?$/u, "");
  name = name.replace(/\s+/g, "");
  return name.slice(0, 24);
}

export function buildVideoSearchQuery(dishName: string): string {
  const name = sanitizeDishName(dishName);
  if (!name) return SEARCH_SUFFIX;
  return `${name} ${SEARCH_SUFFIX}`.trim();
}

export function bilibiliSearchUrl(dishName: string): string {
  const query = buildVideoSearchQuery(dishName);
  return `https://search.bilibili.com/all?keyword=${encodeURIComponent(query)}`;
}

export function douyinSearchUrl(dishName: string): string {
  const query = buildVideoSearchQuery(dishName);
  return `https://www.douyin.com/search/${encodeURIComponent(query)}`;
}

export function videoSearchUrl(platform: VideoPlatform, dishName: string): string {
  return platform === "bilibili" ? bilibiliSearchUrl(dishName) : douyinSearchUrl(dishName);
}

export function openVideoSearch(platform: VideoPlatform, dishName: string): void {
  const name = sanitizeDishName(dishName);
  if (!name) return;
  window.open(videoSearchUrl(platform, name), "_blank", "noopener,noreferrer");
}

function isValidDishName(name: string): boolean {
  const clean = sanitizeDishName(name);
  return clean.length >= 2 && !GENERIC_TITLES.has(clean);
}

/** Split meal-plan lines like "香菇青菜、红烧肉" into individual dish names. */
export function splitDishNames(text: string): string[] {
  if (!text?.trim()) return [];

  const cleaned = text
    .replace(/\*\*/g, "")
    .replace(/[（(][^）)]*[）)]/g, "")
    .trim();

  const parts = cleaned
    .split(/[、，,；;|/]+/)
    .map((part) => sanitizeDishName(part))
    .filter((part) => isValidDishName(part));

  return [...new Set(parts)];
}

/** Extract dish names from meal-plan body (comma list, **bold**, or numbered items). */
export function extractDishNamesFromText(text: string): string[] {
  const fromList = splitDishNames(text);
  if (fromList.length) return fromList;

  const bold = [...text.matchAll(/\*\*([^*\n]{2,20})\*\*/g)]
    .map((m) => sanitizeDishName(m[1]))
    .filter(isValidDishName);
  if (bold.length) return [...new Set(bold)];

  const numbered = [...text.matchAll(/(?:^|\n)\d+[、.)．]\s*([^\n：:*]{2,16})/g)]
    .map((m) => sanitizeDishName(m[1]))
    .filter(isValidDishName);
  return [...new Set(numbered)];
}

/** Extract dish name from user question like "糖醋排骨怎么做". */
export function extractDishNameFromQuestion(question: string): string {
  const q = (question || "").trim();
  const patterns = [
    /([\u4e00-\u9fff]{2,12})(?=怎么做|的做法|如何做|如何做)/,
    /([\u4e00-\u9fff]{2,12})(?=需要哪些食材|需要什么食材|需要哪些|需要什么)/,
    /(?:请问|帮我)?([\u4e00-\u9fff]{2,12})的?(?:做法|食谱)/
  ];
  for (const pattern of patterns) {
    const match = q.match(pattern);
    if (match?.[1]) {
      const name = sanitizeDishName(match[1]);
      if (name && !GENERIC_TITLES.has(name)) return name;
    }
  }
  return "";
}

/** Best-effort dish name for media buttons and cover image. */
export function resolveDishNameForCard(
  userQuestion: string,
  cardTitle?: string,
  content?: string
): string {
  return (
    extractDishNameFromQuestion(userQuestion) ||
    resolveRecipeDishName(cardTitle, content) ||
    sanitizeDishName(cardTitle || "")
  );
}

/** Resolve a searchable dish name from card title or message body. */
export function resolveRecipeDishName(cardTitle?: string, content?: string): string {
  const title = sanitizeDishName(cardTitle || "");
  if (isValidDishName(title) && title.length <= 16) {
    return title;
  }

  const text = content || "";
  const patterns = [
    /分享[^的\n]*的([\u4e00-\u9fff]{2,10})(?:图片|照片|成品)?/,
    /(?:看到|识别)[^「"\n]*[「"]?([\u4e00-\u9fff]{2,10})(?:图片|照片)?/,
    /\*\*([\u4e00-\u9fff]{2,12})\*\*/,
    /##\s*([\u4e00-\u9fff]{2,12})/,
    /([\u4e00-\u9fff]{2,12})(?=怎么做|的做法|食谱)/
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match?.[1]) {
      const candidate = sanitizeDishName(match[1]);
      if (isValidDishName(candidate)) {
        return candidate;
      }
    }
  }

  return isValidDishName(title) ? title : "";
}

export function resolveMediaBase(): string {
  const base = import.meta.env.VITE_API_BASE_URL || "";
  return base.replace(/\/$/, "");
}

export function absoluteUploadUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const base = resolveMediaBase();
  return base ? `${base}${path.startsWith("/") ? path : `/${path}`}` : path;
}

export async function fetchDishImageUrl(dishName: string): Promise<string | null> {
  const name = sanitizeDishName(dishName);
  if (!name) return null;
  const base = resolveMediaBase();
  const url = `${base}/api/v1/media/dish-image?dish_name=${encodeURIComponent(name)}`;
  const resp = await fetch(url);
  if (!resp.ok) return null;
  const data = (await resp.json()) as { image_url?: string };
  return data.image_url ? absoluteUploadUrl(data.image_url) : null;
}
