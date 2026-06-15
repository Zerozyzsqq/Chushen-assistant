<template>
  <div class="user-hub" :class="{ 'user-hub--full': full }">
    <div class="uh-tabs">
      <button
        type="button"
        class="uh-tab"
        :class="{ active: activeTab === 'fridge' }"
        @click="activeTab = 'fridge'"
      >
        <i class="ti ti-fridge" aria-hidden="true"></i>
        虚拟冰箱
        <span v-if="profile.virtualFridge.items.length" class="uh-badge">
          {{ profile.virtualFridge.items.length }}
        </span>
        <span v-if="expiringCount" class="uh-badge uh-badge-warn">{{ expiringCount }} 临期</span>
      </button>
      <button
        type="button"
        class="uh-tab"
        :class="{ active: activeTab === 'profile' }"
        @click="activeTab = 'profile'"
      >
        <i class="ti ti-heart-rate-monitor" aria-hidden="true"></i>
        饮食画像
      </button>
    </div>

    <div v-if="activeTab === 'fridge'" class="uh-panel uh-panel-fridge">
      <div class="uh-section-intro">
        拍照识食材并确认后会自动入库；系统按常识推算保质期，临期时在对话区提醒。
      </div>

      <div v-if="!profile.virtualFridge.items.length" class="uh-empty-state">
        <i class="ti ti-box-off" aria-hidden="true"></i>
        <p>冰箱还是空的</p>
        <span>识食材入库，或下方手动添加</span>
      </div>

      <div v-else class="uh-fridge-grid">
        <div
          v-for="item in profile.virtualFridge.items"
          :key="item.id"
          class="uh-fridge-card"
          :class="expiryClass(item.expiresAt)"
        >
          <div class="uh-card-top">
            <span class="uh-fi-name">{{ item.name }}</span>
            <button type="button" class="uh-fi-del" aria-label="移除" @click="emitRemove(item.id)">
              <i class="ti ti-trash" aria-hidden="true"></i>
            </button>
          </div>
          <div class="uh-card-meta">
            <span class="uh-storage-tag">{{ item.storage === "freezer" ? "冷冻" : "冷藏" }}</span>
            <span>到期 {{ formatExpiry(item.expiresAt) }}</span>
          </div>
          <div class="uh-card-status">{{ expiryLabel(item.expiresAt) }}</div>
        </div>
      </div>

      <div class="uh-add-block">
        <div class="uh-label">手动添加食材</div>
        <div class="uh-add-row">
          <input
            v-model="newItemName"
            type="text"
            placeholder="输入食材名称，回车添加"
            @keydown.enter.prevent="addManualItem"
          />
          <button type="button" class="uh-add-btn" @click="addManualItem">添加</button>
        </div>
      </div>

      <button
        v-if="profile.virtualFridge.items.length"
        type="button"
        class="uh-plan-btn"
        @click="emitPlanFromFridge"
      >
        <i class="ti ti-calendar-event" aria-hidden="true"></i>
        用冰箱食材推荐菜谱
      </button>
    </div>

    <div v-else class="uh-panel uh-panel-profile">
      <div class="uh-section-intro">
        配置后，图谱推荐与「怎么做」回答会自动避开禁忌、给出食材替换与健康调整说明。
      </div>

      <div class="uh-profile-block">
        <div class="uh-block-title">饮食目标</div>
        <div class="uh-chips">
          <button
            v-for="opt in dietGoalOptions"
            :key="opt"
            type="button"
            class="uh-chip"
            :class="{ active: profile.preferences.goals.includes(opt) }"
            @click="toggleGoal(opt)"
          >
            {{ opt }}
          </button>
        </div>
      </div>

      <div class="uh-profile-block">
        <div class="uh-block-title">健康状况</div>
        <div class="uh-chips">
          <button
            v-for="opt in healthOptions"
            :key="opt"
            type="button"
            class="uh-chip"
            :class="{ active: profile.preferences.healthConditions.includes(opt) }"
            @click="toggleHealth(opt)"
          >
            {{ opt }}
          </button>
        </div>
      </div>

      <div class="uh-profile-block">
        <div class="uh-block-title">需避开食材</div>
        <div class="uh-chips">
          <button
            v-for="opt in allergenOptions"
            :key="opt"
            type="button"
            class="uh-chip uh-chip-warn"
            :class="{ active: profile.preferences.avoidIngredients.includes(opt) }"
            @click="toggleAvoid(opt)"
          >
            {{ opt }}
          </button>
        </div>
      </div>

      <div class="uh-profile-block uh-profile-row">
        <div>
          <div class="uh-block-title">默认用餐人数</div>
          <div class="uh-block-hint">识食材推荐菜谱时使用</div>
        </div>
        <div class="uh-stepper">
          <button type="button" aria-label="减少" @click="adjustHousehold(-1)">−</button>
          <span>{{ profile.household.size }} 人</span>
          <button type="button" aria-label="增加" @click="adjustHousehold(1)">+</button>
        </div>
      </div>

      <div class="uh-profile-block">
        <div class="uh-block-title">补充说明</div>
        <textarea
          v-model="localNotes"
          rows="3"
          placeholder="例如：晚餐尽量 30 分钟内搞定；少油少盐"
          @blur="saveNotes"
        />
      </div>

      <div v-if="profileSummary" class="uh-summary">
        <i class="ti ti-shield-check" aria-hidden="true"></i>
        {{ profileSummary }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  COMMON_ALLERGENS,
  DIET_GOAL_OPTIONS,
  getExpiryAlerts,
  HEALTH_CONDITION_OPTIONS,
  upsertFridgeItems,
  type ChushenProfile
} from "../stores/userProfile";
import { daysUntil, formatExpiryDate } from "../utils/shelfLife";

const props = withDefaults(
  defineProps<{
    profile: ChushenProfile;
    full?: boolean;
  }>(),
  { full: false }
);

const emit = defineEmits<{
  update: [profile: ChushenProfile];
  planFromFridge: [ingredients: string[]];
}>();

const activeTab = ref<"fridge" | "profile">("fridge");
const newItemName = ref("");
const localNotes = ref(props.profile.preferences.notes);

const dietGoalOptions = DIET_GOAL_OPTIONS;
const healthOptions = HEALTH_CONDITION_OPTIONS;
const allergenOptions = COMMON_ALLERGENS;

const expiringCount = computed(() => getExpiryAlerts(props.profile, 2).length);

const profileSummary = computed(() => {
  const p = props.profile.preferences;
  const parts: string[] = [];
  if (p.goals.length) parts.push(`目标：${p.goals.join("、")}`);
  if (p.healthConditions.length) parts.push(`注意：${p.healthConditions.join("、")}`);
  if (p.avoidIngredients.length) parts.push(`避开：${p.avoidIngredients.join("、")}`);
  return parts.length ? `已启用健康护栏 — ${parts.join("；")}` : "";
});

watch(
  () => props.profile.preferences.notes,
  (v) => {
    localNotes.value = v;
  }
);

function emitUpdate(next: ChushenProfile) {
  emit("update", next);
}

function formatExpiry(iso: string) {
  return formatExpiryDate(iso);
}

function expiryLabel(iso: string) {
  const d = daysUntil(iso);
  if (d < 0) return `已过期 ${Math.abs(d)} 天`;
  if (d === 0) return "今天到期";
  if (d === 1) return "明天到期";
  return `还有 ${d} 天`;
}

function expiryClass(iso: string) {
  const d = daysUntil(iso);
  if (d < 0) return "expired";
  if (d <= 1) return "urgent";
  if (d <= 3) return "soon";
  return "";
}

function emitRemove(id: string) {
  emitUpdate({
    ...props.profile,
    virtualFridge: {
      items: props.profile.virtualFridge.items.filter((i) => i.id !== id),
      updatedAt: new Date().toISOString()
    }
  });
}

function addManualItem() {
  const name = newItemName.value.trim();
  if (!name) return;
  emitUpdate(upsertFridgeItems(props.profile, [name], "manual"));
  newItemName.value = "";
}

function emitPlanFromFridge() {
  const names = props.profile.virtualFridge.items.map((i) => i.name);
  if (names.length) emit("planFromFridge", names);
}

function toggleInList(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

function toggleGoal(opt: string) {
  emitUpdate({
    ...props.profile,
    preferences: {
      ...props.profile.preferences,
      goals: toggleInList(props.profile.preferences.goals, opt)
    }
  });
}

function toggleHealth(opt: string) {
  emitUpdate({
    ...props.profile,
    preferences: {
      ...props.profile.preferences,
      healthConditions: toggleInList(props.profile.preferences.healthConditions, opt)
    }
  });
}

function toggleAvoid(opt: string) {
  emitUpdate({
    ...props.profile,
    preferences: {
      ...props.profile.preferences,
      avoidIngredients: toggleInList(props.profile.preferences.avoidIngredients, opt)
    }
  });
}

function adjustHousehold(delta: number) {
  const size = Math.min(12, Math.max(1, props.profile.household.size + delta));
  emitUpdate({
    ...props.profile,
    household: { ...props.profile.household, size }
  });
}

function saveNotes() {
  emitUpdate({
    ...props.profile,
    preferences: { ...props.profile.preferences, notes: localNotes.value.trim() }
  });
}
</script>
