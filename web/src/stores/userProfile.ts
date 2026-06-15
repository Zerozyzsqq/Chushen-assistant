/** Single-user profile — localStorage only, no auth. */

import { estimateShelfLife } from "../utils/shelfLife";

export type MealPlanDefault = "today_lunch" | "today_dinner" | "week";
export type SpiceLevel = "none" | "mild" | "medium" | "hot";
export type FridgeStorage = "fridge" | "freezer";
export type FridgeSource = "manual" | "vision" | "recipe";

export interface FridgeItem {
  id: string;
  name: string;
  quantity?: string;
  addedAt: string;
  expiresAt: string;
  storage: FridgeStorage;
  source: FridgeSource;
}

export interface DietaryProfile {
  goals: string[];
  avoidIngredients: string[];
  healthConditions: string[];
  spiceLevel: SpiceLevel;
  notes: string;
}

export interface ChushenProfile {
  version: 1;
  deviceId: string;
  household: {
    size: number;
    defaultMealPlan: MealPlanDefault;
  };
  virtualFridge: {
    items: FridgeItem[];
    updatedAt: string;
  };
  preferences: DietaryProfile;
}

const STORAGE_KEY = "chushen_profile_v1";
const LEGACY_STORAGE_KEYS = ["shidian_profile_v1", "gustobot_profile_v1"];

export const DIET_GOAL_OPTIONS = ["减脂", "高蛋白", "低脂", "控糖", "增肌", "清淡"];
export const HEALTH_CONDITION_OPTIONS = ["痛风", "高血压", "糖尿病", "高尿酸", "肠胃敏感"];
export const COMMON_ALLERGENS = ["海鲜", "花生", "牛奶", "鸡蛋", "大豆", "麸质"];

function defaultProfile(): ChushenProfile {
  const now = new Date().toISOString();
  return {
    version: 1,
    deviceId: crypto.randomUUID(),
    household: { size: 2, defaultMealPlan: "today_dinner" },
    virtualFridge: { items: [], updatedAt: now },
    preferences: {
      goals: [],
      avoidIngredients: [],
      healthConditions: [],
      spiceLevel: "mild",
      notes: ""
    }
  };
}

export function loadProfile(): ChushenProfile {
  try {
    let raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      for (const legacyKey of LEGACY_STORAGE_KEYS) {
        raw = localStorage.getItem(legacyKey);
        if (raw) {
          localStorage.setItem(STORAGE_KEY, raw);
          break;
        }
      }
    }
    if (!raw) return defaultProfile();
    const parsed = JSON.parse(raw) as ChushenProfile;
    if (parsed.version !== 1) return defaultProfile();
    return {
      ...defaultProfile(),
      ...parsed,
      household: { ...defaultProfile().household, ...parsed.household },
      virtualFridge: {
        items: Array.isArray(parsed.virtualFridge?.items) ? parsed.virtualFridge.items : [],
        updatedAt: parsed.virtualFridge?.updatedAt || new Date().toISOString()
      },
      preferences: { ...defaultProfile().preferences, ...parsed.preferences }
    };
  } catch {
    return defaultProfile();
  }
}

export function saveProfile(profile: ChushenProfile): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
}

export function profileForApi(profile: ChushenProfile) {
  const p = profile.preferences;
  return {
    goals: p.goals,
    avoid_ingredients: p.avoidIngredients,
    health_conditions: p.healthConditions,
    spice_level: p.spiceLevel,
    notes: p.notes || undefined
  };
}

export function upsertFridgeItems(
  profile: ChushenProfile,
  names: string[],
  source: FridgeSource = "vision"
): ChushenProfile {
  const now = new Date();
  const items = [...profile.virtualFridge.items];

  for (const rawName of names) {
    const name = rawName.trim();
    if (!name) continue;
    const shelf = estimateShelfLife(name);
    const expiresAt = new Date(now);
    expiresAt.setDate(expiresAt.getDate() + shelf.days);

    const existingIdx = items.findIndex(
      (item) => item.name === name && item.storage === shelf.storage
    );
    const entry: FridgeItem = {
      id: existingIdx >= 0 ? items[existingIdx].id : crypto.randomUUID(),
      name,
      addedAt: now.toISOString(),
      expiresAt: expiresAt.toISOString(),
      storage: shelf.storage,
      source
    };
    if (existingIdx >= 0) items[existingIdx] = entry;
    else items.unshift(entry);
  }

  return {
    ...profile,
    virtualFridge: { items: items.slice(0, 80), updatedAt: now.toISOString() }
  };
}

export function removeFridgeItem(profile: ChushenProfile, id: string): ChushenProfile {
  return {
    ...profile,
    virtualFridge: {
      items: profile.virtualFridge.items.filter((i) => i.id !== id),
      updatedAt: new Date().toISOString()
    }
  };
}

export interface ExpiryAlert {
  item: FridgeItem;
  daysLeft: number;
  label: string;
}

export function getExpiryAlerts(profile: ChushenProfile, withinDays = 2): ExpiryAlert[] {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const alerts: ExpiryAlert[] = [];

  for (const item of profile.virtualFridge.items) {
    const exp = new Date(item.expiresAt);
    exp.setHours(0, 0, 0, 0);
    const daysLeft = Math.ceil((exp.getTime() - now.getTime()) / 86400000);
    if (daysLeft <= withinDays) {
      alerts.push({
        item,
        daysLeft,
        label:
          daysLeft < 0
            ? `已过期 ${Math.abs(daysLeft)} 天`
            : daysLeft === 0
              ? "今天到期"
              : `还有 ${daysLeft} 天到期`
      });
    }
  }

  return alerts.sort((a, b) => a.daysLeft - b.daysLeft);
}
