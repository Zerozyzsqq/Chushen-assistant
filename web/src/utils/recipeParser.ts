/** Parse graphrag / LLM recipe replies into structured card data. */

import {
  extractDishNameFromQuestion,
  sanitizeDishName
} from "./videoSearch";

export interface IngredientRow {
  name: string;
  amount: string;
}

export interface StepRow {
  title?: string;
  detail: string;
}

export interface RecipeSection {
  label: string;
  text: string;
  items: string[];
}

export interface RecipeVariant {
  title: string;
  ingredients: IngredientRow[];
  steps: StepRow[];
  sections: RecipeSection[];
}

export interface ParsedRecipe {
  cardTitle: string;
  dishName: string;
  intro: string;
  ingredients: IngredientRow[];
  steps: StepRow[];
  sections: RecipeSection[];
  variants: RecipeVariant[];
}

function parseBoldTitleLine(line: string): string {
  const m = line.match(/^\*\*([^*]+)\*\*$/);
  return m ? m[1].trim() : "";
}

const SECTION_LABELS = [
  "核心食材",
  "主要食材",
  "主食材",
  "辅料",
  "所需食材",
  "做法重点",
  "关键步骤",
  "做法步骤",
  "烹饪步骤",
  "做法",
  "风味特点",
  "口味特点",
  "耗时",
  "烹饪耗时",
  "小贴士",
  "说明"
];

const SKIP_LINE = /^(厨友|亲爱的|您好|已经|以下|根据|图谱|检索|参考)/;

function stripMarkdown(text: string): string {
  return (text || "")
    .replace(/\*\*/g, "")
    .replace(/__/g, "")
    .replace(/^[-*•]\s*/, "")
    .trim();
}

function parseStepLine(raw: string): StepRow {
  const line = stripMarkdown(raw);
  const titled = line.match(/^(.{2,14}?)[：:]\s*(.+)$/);
  if (titled && !SECTION_LABELS.includes(titled[1])) {
    return { title: titled[1].trim(), detail: titled[2].trim() };
  }
  return { detail: line };
}

function parseIngredientPhrase(text: string): IngredientRow[] {
  const cleaned = stripMarkdown(text);
  if (!cleaned) return [];

  return cleaned
    .split(/[、，,；;|/]+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const wrapped = part.match(/^(.+?)[（(]([^）)]+)[）)]$/);
      if (wrapped) {
        return { name: wrapped[1].trim(), amount: wrapped[2].trim() };
      }
      const colon = part.match(/^(.{1,12}?)[：:]\s*(.+)$/);
      if (colon) {
        return { name: colon[1].trim(), amount: colon[2].trim() };
      }
      return { name: part, amount: "适量" };
    })
    .filter((row) => row.name.length >= 1);
}

function splitIntoSteps(text: string): StepRow[] {
  const cleaned = stripMarkdown(text);
  if (!cleaned) return [];

  const numbered = [...cleaned.matchAll(/(?:^|\s)(\d+)[、.)．]\s*([^；;。\d]+)/g)];
  if (numbered.length >= 2) {
    return numbered.map((m) => parseStepLine(m[2].trim()));
  }

  const chunks = cleaned
    .split(/[；;。]+/)
    .map((s) => s.trim())
    .filter((s) => s.length >= 4);

  if (chunks.length >= 2) {
    return chunks.map((c) => ({ detail: c }));
  }

  return [{ detail: cleaned }];
}

function extractSection(line: string): { label: string; value: string } | null {
  const normalized = stripMarkdown(line).replace(/^[-*•]\s*/, "");
  for (const label of SECTION_LABELS) {
    const re = new RegExp(`^${label}[：:]\\s*(.+)$`);
    const match = normalized.match(re);
    if (match) {
      return { label, value: match[1].trim() };
    }
  }
  return null;
}

function sectionToRows(label: string, value: string): {
  ingredients: IngredientRow[];
  steps: StepRow[];
  section: RecipeSection;
} {
  const ingredients: IngredientRow[] = [];
  const steps: StepRow[] = [];

  if (/食材|辅料|原料/.test(label)) {
    ingredients.push(...parseIngredientPhrase(value));
    return {
      ingredients,
      steps,
      section: {
        label,
        text: value,
        items: ingredients.map((i) => (i.amount ? `${i.name}（${i.amount}）` : i.name))
      }
    };
  }

  if (/做法|步骤|重点/.test(label)) {
    steps.push(...splitIntoSteps(value));
    return {
      ingredients,
      steps,
      section: { label, text: value, items: steps.map((s) => s.detail) }
    };
  }

  return {
    ingredients,
    steps,
    section: {
      label,
      text: value,
      items: value.split(/[、，,；;]/).map((s) => s.trim()).filter(Boolean)
    }
  };
}

function parseBlock(title: string, blockLines: string[]): RecipeVariant {
  const ingredients: IngredientRow[] = [];
  const steps: StepRow[] = [];
  const sections: RecipeSection[] = [];

  for (const line of blockLines) {
    if (!line || SKIP_LINE.test(line)) continue;

    const sec = extractSection(line);
    if (sec) {
      const parsed = sectionToRows(sec.label, sec.value);
      ingredients.push(...parsed.ingredients);
      steps.push(...parsed.steps);
      sections.push(parsed.section);
      continue;
    }

    const stepMatch = line.match(/^(\d+)[:：.、)\]]\s*(.+)$/);
    if (stepMatch) {
      steps.push(parseStepLine(stepMatch[2]));
    }
  }

  return {
    title: stripMarkdown(title),
    ingredients: sections.some((s) => /食材|辅料|原料/.test(s.label)) ? [] : ingredients,
    steps: sections.some((s) => /做法|步骤|重点/.test(s.label)) ? [] : steps,
    sections
  };
}

function splitIntoVariants(content: string): Array<{ title: string; body: string }> {
  const text = content.replace(/\r\n/g, "\n").trim();
  const variants: Array<{ title: string; body: string }> = [];

  const headingParts = text.split(/\n(?=###\s+)/);
  if (headingParts.length > 1) {
    for (const part of headingParts) {
      const m = part.match(/^###\s*(.+)\n([\s\S]*)$/);
      if (m) variants.push({ title: m[1].trim(), body: m[2].trim() });
    }
    if (variants.length) return variants;
  }

  const boldBlocks = [
    ...text.matchAll(/\*\*([^*\n]{2,24})\*\*\s*\n([\s\S]*?)(?=\n\*\*[^*\n]{2,24}\*\*|\n##\s|$)/g)
  ];
  if (boldBlocks.length > 1) {
    for (const m of boldBlocks) {
      variants.push({ title: m[1].trim(), body: m[2].trim() });
    }
    return variants;
  }

  const inlineBold = [
    ...text.matchAll(/\*\*([^*\n]{2,24})\*\*\s*\n?([\s\S]*?)(?=\*\*[^*\n]{2,24}\*\*|$)/g)
  ];
  if (inlineBold.length > 1) {
    for (const m of inlineBold) {
      variants.push({ title: m[1].trim(), body: m[2].trim() });
    }
    return variants;
  }

  const numberedBlocks = [...text.matchAll(/\n(\d+)[.、．]\s*\*\*([^*]+)\*\*\s*\n([\s\S]*?)(?=\n\d+[.、．]\s*\*\*|$)/g)];
  if (numberedBlocks.length > 1) {
    for (const m of numberedBlocks) {
      variants.push({ title: m[2].trim(), body: m[3].trim() });
    }
    return variants;
  }

  return [{ title: "", body: text }];
}

export function parseRecipeContent(content: string, userQuestion: string): ParsedRecipe {
  const lines = content
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const introLines: string[] = [];
  const mainLines: string[] = [];
  for (const line of lines) {
    if (SKIP_LINE.test(line) && !extractSection(line)) {
      introLines.push(stripMarkdown(line));
    } else {
      mainLines.push(line);
    }
  }

  const mainText = mainLines.join("\n");
  const rawVariants = splitIntoVariants(mainText);

  const variants: RecipeVariant[] = rawVariants.map((v) => {
    const blockLines = v.body.split("\n").map((l) => l.trim()).filter(Boolean);
    let title = v.title || "";
    const filtered: string[] = [];
    for (const line of blockLines) {
      const boldTitle = parseBoldTitleLine(line);
      if (boldTitle && !title) {
        title = boldTitle;
        continue;
      }
      filtered.push(line);
    }
    return parseBlock(title, filtered);
  });

  const primary = variants[0] || parseBlock("", mainLines);
  const dishName =
    extractDishNameFromQuestion(userQuestion) ||
    sanitizeDishName(primary.title) ||
    sanitizeDishName(content.match(/\*\*([\u4e00-\u9fff]{2,16})\*\*/)?.[1] || "") ||
    sanitizeDishName(content.match(/(?:菜名|菜品)[：:]\s*([^\n，,。]+)/)?.[1] || "");

  const cardTitle = dishName || primary.title || truncateQuestion(userQuestion);

  const ingredients = [...primary.ingredients];
  const steps = [...primary.steps];
  const sections = [...primary.sections];

  if (!ingredients.length && !steps.length && !sections.length) {
    for (const line of mainLines) {
      const sec = extractSection(line);
      if (sec) {
        const parsed = sectionToRows(sec.label, sec.value);
        ingredients.push(...parsed.ingredients);
        steps.push(...parsed.steps);
        sections.push(parsed.section);
      }
    }
  }

  const hasIngredientSection = sections.some((s) => /食材|辅料|原料/.test(s.label));
  const hasStepSection = sections.some((s) => /做法|步骤|重点/.test(s.label));
  const multiVariant = variants.length > 1;

  return {
    cardTitle,
    dishName: dishName || cardTitle,
    intro: introLines.slice(0, 2).join(""),
    ingredients: multiVariant || hasIngredientSection ? [] : ingredients,
    steps: multiVariant || hasStepSection ? [] : steps,
    sections: multiVariant ? [] : sections,
    variants: multiVariant ? variants : []
  };
}

function truncateQuestion(q: string): string {
  const t = q.trim();
  return t.length > 14 ? `${t.slice(0, 14)}…` : t;
}

export function normalizeSteps(steps?: Array<StepRow | string>): StepRow[] {
  if (!steps?.length) return [];
  return steps.map((step) => (typeof step === "string" ? parseStepLine(step) : step));
}

export function recipeHasCookingSteps(data: {
  steps?: StepRow[];
  sections?: RecipeSection[];
  variants?: RecipeVariant[];
}): boolean {
  if (data.steps?.length) return true;
  if (data.sections?.some((s) => /做法|步骤/.test(s.label))) return true;
  if (
    data.variants?.some(
      (v) => v.steps.length || v.sections.some((s) => /做法|步骤/.test(s.label))
    )
  ) {
    return true;
  }
  return false;
}
