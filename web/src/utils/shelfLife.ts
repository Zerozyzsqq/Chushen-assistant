/** Heuristic shelf-life rules (days) for virtual fridge. */

import type { FridgeStorage } from "../stores/userProfile";

export interface ShelfLifeEstimate {
  days: number;
  storage: FridgeStorage;
  hint: string;
}

interface ShelfRule {
  keywords: string[];
  days: number;
  storage: FridgeStorage;
  hint: string;
}

const RULES: ShelfRule[] = [
  { keywords: ["叶", "生菜", "菠菜", "油菜", "小白菜", "韭菜", "香菜", "芹菜", "空心菜"], days: 3, storage: "fridge", hint: "绿叶菜冷藏约3天" },
  { keywords: ["豆腐", "豆干", "豆皮"], days: 3, storage: "fridge", hint: "豆制品冷藏约3天" },
  { keywords: ["牛奶", "酸奶", "奶酪"], days: 5, storage: "fridge", hint: "乳制品冷藏约5天" },
  { keywords: ["鸡蛋"], days: 14, storage: "fridge", hint: "鸡蛋冷藏约2周" },
  { keywords: ["猪肉", "牛肉", "羊肉", "排骨", "五花"], days: 3, storage: "fridge", hint: "鲜肉冷藏约3天" },
  { keywords: ["鸡", "鸭", "鹅", "禽"], days: 3, storage: "fridge", hint: "禽肉冷藏约3天" },
  { keywords: ["鱼", "虾", "蟹", "贝", "海鲜", "鱿鱼"], days: 2, storage: "fridge", hint: "海鲜冷藏约2天" },
  { keywords: ["土豆", "洋葱", "南瓜", "红薯", "山药"], days: 14, storage: "fridge", hint: "根茎类约2周" },
  { keywords: ["苹果", "梨", "橙", "柚", "香蕉", "葡萄", "草莓", "水果"], days: 5, storage: "fridge", hint: "水果冷藏约5天" },
  { keywords: ["冷冻", "冰鲜"], days: 30, storage: "freezer", hint: "冷冻约30天" },
  { keywords: ["香肠", "火腿", "培根"], days: 7, storage: "fridge", hint: "加工肉冷藏约7天" },
  { keywords: ["蘑菇", "菌"], days: 5, storage: "fridge", hint: "菌菇约5天" },
  { keywords: ["番茄", "黄瓜", "茄子", "青椒", "辣椒", "胡萝卜", "西兰花", "花菜", "白菜"], days: 7, storage: "fridge", hint: "常见蔬菜约7天" }
];

export function estimateShelfLife(name: string): ShelfLifeEstimate {
  const normalized = name.trim();
  for (const rule of RULES) {
    if (rule.keywords.some((kw) => normalized.includes(kw))) {
      return { days: rule.days, storage: rule.storage, hint: rule.hint };
    }
  }
  return { days: 7, storage: "fridge", hint: "默认冷藏约7天" };
}

export function formatExpiryDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export function daysUntil(iso: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const exp = new Date(iso);
  exp.setHours(0, 0, 0, 0);
  return Math.ceil((exp.getTime() - now.getTime()) / 86400000);
}
