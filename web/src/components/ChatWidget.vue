<template>
  <div class="page-shell">
    <div class="wrap">
      <!-- 左侧会话栏 -->
      <aside class="left">
        <div class="brand">
          <div class="brand-icon">
            <i class="ti ti-bowl-chopsticks" aria-hidden="true"></i>
          </div>
          <div>
            <div class="brand-name">厨神助手</div>
            <div class="brand-sub">中华菜谱 · 智能问答</div>
          </div>
        </div>

        <button
          type="button"
          class="kitchen-nav-btn"
          :class="{ active: mainView === 'kitchen' }"
          @click="openKitchen"
        >
          <i class="ti ti-fridge" aria-hidden="true"></i>
          我的厨房
          <span v-if="userProfile.virtualFridge.items.length" class="nav-badge">
            {{ userProfile.virtualFridge.items.length }}
          </span>
        </button>

        <button
          type="button"
          class="new-chat-btn"
          :class="{ active: mainView === 'chat' }"
          @click="startNewChat"
        >
          <i class="ti ti-plus" aria-hidden="true"></i>
          新建对话
        </button>

        <div class="history-scroll">
          <template v-for="group in historyGroups" :key="group.label">
            <div v-if="group.items.length" class="left-section">{{ group.label }}</div>
            <div
              v-for="item in group.items"
              :key="item.id"
              class="hist-item"
              :class="{ active: mainView === 'chat' && item.id === state.activeHistoryId }"
              @click="loadHistory(item.id)"
            >
              <i class="ti ti-message" aria-hidden="true"></i>
              <span class="title">{{ item.title }}</span>
              <span class="htag" :class="tagClass(item.tag)">{{ tagLabel(item.tag) }}</span>
              <button
                type="button"
                class="hist-del"
                aria-label="删除对话"
                title="删除对话"
                @click.stop="deleteHistory(item.id)"
              >
                <i class="ti ti-trash" aria-hidden="true"></i>
              </button>
            </div>
          </template>
          <div v-if="!historyList.length" class="left-section">暂无历史会话</div>
          <button
            v-if="historyList.length"
            type="button"
            class="clear-history-btn"
            @click="clearAllHistory"
          >
            <i class="ti ti-trash" aria-hidden="true"></i>
            清空全部记录
          </button>
        </div>

        <div class="feature-pills">
          <button
            v-for="pill in featurePills"
            :key="pill.label"
            type="button"
            class="fpill"
            @click="sendSuggestion(pill.prompt)"
          >
            <i :class="pill.icon" aria-hidden="true"></i>
            {{ pill.label }}
          </button>
        </div>
      </aside>

      <!-- 主内容区：对话 或 我的厨房 -->
      <main class="right">
        <template v-if="mainView === 'kitchen'">
          <div class="kitchen-full">
            <div class="kitchen-full-head">
              <div class="kitchen-head-icon">
                <i class="ti ti-fridge" aria-hidden="true"></i>
              </div>
              <div>
                <div class="kitchen-title">我的厨房</div>
                <div class="kitchen-sub">虚拟冰箱 · 饮食画像 · 临期提醒 · 健康护栏</div>
              </div>
              <button type="button" class="kitchen-back-btn" @click="mainView = 'chat'">
                <i class="ti ti-message" aria-hidden="true"></i>
                返回对话
              </button>
            </div>
            <UserHub
              full
              :profile="userProfile"
              @update="updateProfile"
              @plan-from-fridge="startPlanFromFridge"
            />
          </div>
        </template>

        <template v-else>
        <div class="chat-top">
          <div class="chat-top-left">
            <span class="chat-title">{{ chatTitle }}</span>
            <span v-if="currentAgentBadge" class="agent-badge" :class="currentAgentBadge.cls">
              <i :class="currentAgentBadge.icon" aria-hidden="true"></i>
              {{ currentAgentBadge.label }}
            </span>
          </div>
          <div class="chat-top-right">
            <button type="button" class="top-btn" aria-label="我的厨房" @click="openKitchen">
              <i class="ti ti-fridge" aria-hidden="true"></i>
            </button>
            <button type="button" class="top-btn" aria-label="新建对话" @click="startNewChat">
              <i class="ti ti-plus" aria-hidden="true"></i>
            </button>
          </div>
        </div>

        <div v-if="expiryAlerts.length" class="expiry-banner">
          <div v-for="alert in expiryAlerts.slice(0, 3)" :key="alert.item.id" class="expiry-row">
            <span class="expiry-text">
              <i class="ti ti-bell-ringing" aria-hidden="true"></i>
              {{ alert.item.name }}{{ alert.label }}，今晚做点什么？
            </span>
            <button
              type="button"
              class="expiry-action"
              @click="sendSuggestion(`用${alert.item.name}推荐一道今晚的家常菜`)"
            >
              推荐菜谱
            </button>
          </div>
        </div>

        <div ref="messageContainer" class="msgs">
          <div v-if="conversationStartedAt" class="sys-msg">
            对话开始于 {{ conversationStartedAt }}
          </div>

          <div v-if="!messages.length && !isTyping" class="sys-msg">
            问做法、查典故、聊饮食文化…
          </div>

          <template v-for="(message, index) in messages" :key="index">
            <div v-if="message.role === 'user'" class="msg-user">
              <div class="av av-user">我</div>
              <div class="bubble-wrap user-wrap">
                <div v-if="message.hasImage" class="user-attach-tag">
                  <i class="ti ti-camera" aria-hidden="true"></i>
                  已附图片
                </div>
                <div class="bubble bubble-user">{{ message.content }}</div>
              </div>
            </div>

            <div v-else class="msg-ai">
              <div class="av av-ai">
                <i class="ti ti-bowl-chopsticks" style="font-size: 12px" aria-hidden="true"></i>
              </div>
              <div class="bubble-wrap">
                <div
                  v-if="message.route"
                  class="thinking-strip"
                  style="opacity: 0.85"
                >
                  <span class="tk-label">路由</span>
                  <span class="route-tag">{{ routeLabel(message.route) }}</span>
                </div>

                <div
                  v-if="message.intro"
                  class="bubble bubble-ai"
                  v-html="linkify(message.intro)"
                ></div>

                <div v-if="message.sources?.length" class="source-strip">
                  <span
                    v-for="(source, sIdx) in message.sources.slice(0, 4)"
                    :key="sIdx"
                    class="src-tag"
                  >
                    <i class="ti ti-file-text" aria-hidden="true"></i>
                    {{ formatSource(source) }}
                  </span>
                </div>

                <!-- 文化典故卡片 -->
                <div v-if="message.cardType === 'culture'" class="culture-card">
                  <div class="cc-head">
                    <i class="ti ti-book" aria-hidden="true"></i>
                    <span>饮食典故 · {{ message.cardTitle || "文化解读" }}</span>
                  </div>
                  <div class="cc-body" v-html="linkify(message.cardBody || message.content)"></div>
                  <div v-if="message.tags?.length" class="cc-tags">
                    <span v-for="tag in message.tags" :key="tag" class="cc-tag">{{ tag }}</span>
                  </div>
                </div>

                <!-- 菜谱卡片 -->
                <div v-else-if="message.cardType === 'recipe'" class="recipe-card">
                  <div class="rc-head">
                    <div class="rc-icon">
                      <i class="ti ti-tools-kitchen-2" aria-hidden="true"></i>
                    </div>
                    <span class="rc-title">{{ message.cardTitle || "菜谱详情" }}</span>
                    <span class="rc-diff">{{ message.difficulty || "图谱检索" }}</span>
                  </div>
                  <DishImage v-if="message.dishName" :dish-name="message.dishName" />
                  <div v-if="hasStructuredRecipe(message)" class="rc-body-stack">
                    <p v-if="message.recipeIntro" class="rc-intro">{{ message.recipeIntro }}</p>

                    <div v-if="message.ingredients?.length" class="rc-block">
                      <div class="rc-col-title">主要食材</div>
                      <div class="ing-list">
                        <div
                          v-for="(ing, iIdx) in message.ingredients"
                          :key="`ing-${iIdx}`"
                          class="ing-row"
                        >
                          <span>{{ ing.name }}</span>
                          <span>{{ ing.amount }}</span>
                        </div>
                      </div>
                    </div>

                    <div v-if="message.steps?.length" class="rc-block">
                      <div class="rc-col-title">关键步骤</div>
                      <div class="steps-list">
                        <div
                          v-for="(step, sIdx) in normalizeSteps(message.steps)"
                          :key="`step-${sIdx}`"
                          class="step-row"
                        >
                          <div class="step-num">{{ sIdx + 1 }}</div>
                          <div class="step-text">
                            <span v-if="step.title" class="step-title">{{ step.title }}</span>
                            <span class="step-detail">{{ step.detail }}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div
                      v-for="(sec, secIdx) in message.recipeSections"
                      :key="`sec-${secIdx}`"
                      class="rc-block"
                    >
                      <div class="rc-col-title">{{ sec.label }}</div>
                      <ul v-if="sec.items.length > 1" class="rc-bullet-list">
                        <li v-for="(item, itemIdx) in sec.items" :key="itemIdx">{{ item }}</li>
                      </ul>
                      <p v-else class="rc-section-text">{{ sec.text }}</p>
                    </div>

                    <div
                      v-for="(variant, vIdx) in message.recipeVariants"
                      :key="`variant-${vIdx}`"
                      class="rc-variant"
                    >
                      <div class="rc-variant-title">{{ variant.title }}</div>
                      <div v-if="variant.ingredients.length" class="rc-block">
                        <div class="rc-col-title">食材</div>
                        <div class="ing-list">
                          <div
                            v-for="(ing, iIdx) in variant.ingredients"
                            :key="`v-ing-${iIdx}`"
                            class="ing-row"
                          >
                            <span>{{ ing.name }}</span>
                            <span>{{ ing.amount }}</span>
                          </div>
                        </div>
                      </div>
                      <div v-if="variant.steps.length" class="rc-block">
                        <div class="rc-col-title">步骤</div>
                        <div class="steps-list">
                          <div
                            v-for="(step, sIdx) in normalizeSteps(variant.steps)"
                            :key="`v-step-${sIdx}`"
                            class="step-row"
                          >
                            <div class="step-num">{{ sIdx + 1 }}</div>
                            <div class="step-text">
                              <span v-if="step.title" class="step-title">{{ step.title }}</span>
                              <span class="step-detail">{{ step.detail }}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div v-for="(sec, sIdx) in variant.sections" :key="`v-sec-${sIdx}`" class="rc-block">
                        <div class="rc-col-title">{{ sec.label }}</div>
                        <ul v-if="sec.items.length > 1" class="rc-bullet-list">
                          <li v-for="(item, itemIdx) in sec.items" :key="itemIdx">{{ item }}</li>
                        </ul>
                        <p v-else class="rc-section-text">{{ sec.text }}</p>
                      </div>
                    </div>
                  </div>
                  <div
                    v-else
                    class="rc-body-single rc-markdown"
                    v-html="linkify(message.content)"
                  ></div>
                  <div class="rc-footer">
                    <button type="button" class="rc-btn" @click="sendSuggestion(`还有和${message.cardTitle || '这道菜'}类似的菜吗？`)">
                      <i class="ti ti-search" aria-hidden="true"></i>
                      相似推荐
                    </button>
                    <template v-if="message.dishName">
                      <button
                        type="button"
                        class="rc-btn rc-btn-video"
                        @click="openVideoSearch('bilibili', message.dishName!)"
                      >
                        📺 B站教程
                      </button>
                      <button
                        type="button"
                        class="rc-btn rc-btn-video"
                        @click="openVideoSearch('douyin', message.dishName!)"
                      >
                        📺 抖音教程
                      </button>
                    </template>
                  </div>
                  <div v-if="message.dishName" class="rc-video-hint">
                    视频来自第三方平台搜索结果，点击后将在新标签页打开
                  </div>
                </div>

                <!-- 食材规划结果 -->
                <div v-else-if="message.cardType === 'meal_plan'" class="meal-plan-card">
                  <div class="mpc-head">
                    <i class="ti ti-calendar-event" aria-hidden="true"></i>
                    <span>{{ message.cardTitle || "菜谱推荐" }}</span>
                    <span class="mpc-scope">{{ message.mealPlanLabel }}</span>
                  </div>
                  <div v-if="message.confirmedIngredients?.length" class="mpc-ingredients">
                    <span
                      v-for="(ing, iIdx) in message.confirmedIngredients"
                      :key="iIdx"
                      class="mpc-chip"
                    >{{ ing }}</span>
                  </div>
                  <div v-if="message.dishItems?.length" class="mpc-dishes">
                    <div
                      v-for="(entry, eIdx) in flattenMealPlanDishes(message.dishItems)"
                      :key="`${eIdx}-${entry.name}`"
                      class="mpc-recipe-card"
                    >
                      <div class="mpc-recipe-meal">{{ entry.mealLabel }}</div>
                      <DishImage :dish-name="entry.name" />
                      <div class="mpc-recipe-name">{{ entry.name }}</div>
                      <div class="mpc-recipe-actions">
                        <button
                          type="button"
                          class="rc-btn rc-btn-video"
                          @click="openVideoSearch('bilibili', entry.name)"
                        >
                          📺 B站教程
                        </button>
                        <button
                          type="button"
                          class="rc-btn rc-btn-video"
                          @click="openVideoSearch('douyin', entry.name)"
                        >
                          📺 抖音教程
                        </button>
                      </div>
                    </div>
                  </div>
                  <div v-else class="mpc-body" v-html="linkify(message.cardBody || message.content)"></div>
                  <div v-if="message.dishItems?.length" class="mpc-video-hint">
                    每道菜可跳转 B 站 / 抖音搜索「菜名 教程」，视频由第三方平台提供
                  </div>
                </div>

                <!-- 默认文本 -->
                <div
                  v-else-if="!message.intro"
                  class="bubble bubble-ai"
                  v-html="linkify(message.content)"
                ></div>
              </div>
            </div>
          </template>

          <div v-if="isTyping" class="msg-ai">
            <div class="av av-ai">
              <i class="ti ti-bowl-chopsticks" style="font-size: 12px" aria-hidden="true"></i>
            </div>
            <div class="bubble-wrap">
              <div class="thinking-strip">
                <div class="tk-dot"></div>
                <div class="tk-dot"></div>
                <div class="tk-dot"></div>
                <span class="tk-label">意图分诊与检索中</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="followUpSuggestions.length" class="suggest-row">
          <button
            v-for="(sg, idx) in followUpSuggestions"
            :key="idx"
            type="button"
            class="sg"
            @click="sendSuggestion(sg)"
          >
            {{ sg }} ↗
          </button>
        </div>

        <div v-if="state.attachedKind === 'image' && !ingredientDraft" class="image-attach-bar">
          <span class="iab-label">
            <i class="ti ti-photo" aria-hidden="true"></i>
            {{ state.attachedFileName || "图片已就绪" }}
          </span>
          <button type="button" class="iab-btn iab-primary" @click="startIngredientRecognition">
            识食材推荐菜谱
          </button>
          <button type="button" class="iab-btn" @click="clearAttachment">移除</button>
        </div>

        <div v-if="ingredientDraft" class="ingredient-panel">
          <div class="ip-head">
            <i class="ti ti-carrot" aria-hidden="true"></i>
            <span>识食材 · 规划菜谱 · {{ ingredientDraft.imageName }}</span>
          </div>
          <div class="ip-chips">
            <button
              v-for="(ing, idx) in ingredientDraft.ingredients"
              :key="`${ing}-${idx}`"
              type="button"
              class="ip-chip"
              @click="removeIngredient(idx)"
            >
              {{ ing }}
              <i class="ti ti-x" aria-hidden="true"></i>
            </button>
          </div>
          <div class="ip-add">
            <input
              v-model="ingredientDraft.newIngredient"
              type="text"
              placeholder="补充或修正食材，回车添加"
              @keydown.enter.prevent="addIngredient"
            />
            <button type="button" class="ip-add-btn" @click="addIngredient">添加</button>
          </div>
          <div class="ip-plan">
            <span class="ip-plan-label">用餐人数</span>
            <div class="ip-people-stepper">
              <button type="button" class="ip-step" @click="adjustHousehold(-1)">−</button>
              <span class="ip-people-num">{{ ingredientDraft.householdSize }} 人</span>
              <button type="button" class="ip-step" @click="adjustHousehold(1)">+</button>
            </div>
            <span class="ip-plan-hint">每餐约 {{ dishesPerMeal(ingredientDraft.householdSize) }} 道菜</span>
          </div>
          <div class="ip-plan">
            <span class="ip-plan-label">规划范围</span>
            <button
              v-for="opt in mealPlanOptions"
              :key="opt.value"
              type="button"
              class="ip-plan-btn"
              :class="{ active: ingredientDraft.mealPlan === opt.value }"
              @click="ingredientDraft.mealPlan = opt.value"
            >
              {{ opt.label }}
            </button>
          </div>
          <div class="ip-actions">
            <button type="button" class="ip-cancel" @click="clearIngredientDraft">取消</button>
            <button
              type="button"
              class="ip-confirm"
              :disabled="!ingredientDraft.ingredients.length || isTyping"
              @click="confirmIngredients"
            >
              确认并推荐菜谱
            </button>
          </div>
        </div>

        <div class="input-zone">
          <div v-if="uploadStatus" class="upload-hint">{{ uploadStatus }}</div>
          <form class="input-box" @submit.prevent="sendMessage">
            <textarea
              v-model="userInput"
              rows="1"
              :placeholder="inputPlaceholder"
              :disabled="isTyping"
              @keydown.enter.exact.prevent="sendMessage"
            />
            <div class="itools">
              <label class="itl" aria-label="上传图片">
                <i class="ti ti-camera" aria-hidden="true"></i>
                <input
                  type="file"
                  class="hidden-input"
                  accept=".jpg,.jpeg,.png,.gif,.bmp,.webp,image/*"
                  @change="onFileSelected"
                />
              </label>
              <label class="itl" aria-label="上传文件">
                <i class="ti ti-paperclip" aria-hidden="true"></i>
                <input
                  type="file"
                  class="hidden-input"
                  accept=".txt,.md,.json,.csv,.log,.xlsx,.xls,.pdf,.doc,.docx"
                  @change="onFileSelected"
                />
              </label>
              <button type="submit" class="send" aria-label="发送" :disabled="isTyping || (!userInput.trim() && !state.attachedFilePath)">
                <i class="ti ti-send" aria-hidden="true"></i>
              </button>
            </div>
          </form>
          <div class="input-hint">
            <span class="hint"><i class="ti ti-git-branch" aria-hidden="true"></i>自动分诊路由</span>
            <span class="hint"><i class="ti ti-database" aria-hidden="true"></i>图谱 + 文化库</span>
            <span class="hint"><i class="ti ti-shield-check" aria-hidden="true"></i>护栏过滤已开启</span>
          </div>
        </div>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import axios from "axios";
import {
  parseRecipeContent,
  normalizeSteps,
  recipeHasCookingSteps,
  type IngredientRow,
  type StepRow,
  type RecipeSection,
  type RecipeVariant
} from "../utils/recipeParser";
import {
  openVideoSearch,
  resolveDishNameForCard,
  extractDishNamesFromText
} from "../utils/videoSearch";
import DishImage from "./DishImage.vue";
import UserHub from "./UserHub.vue";
import {
  getExpiryAlerts,
  loadProfile,
  profileForApi,
  saveProfile,
  upsertFridgeItems,
  type ChushenProfile
} from "../stores/userProfile";
import "../styles/recipe-agent.scss";

interface DishItem {
  title: string;
  body: string;
  dishNames?: string[];
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  hasImage?: boolean;
  route?: string | null;
  routeLogic?: string | null;
  sources?: Array<Record<string, unknown>>;
  cardType?: "recipe" | "culture" | "meal_plan" | null;
  cardTitle?: string;
  cardBody?: string;
  dishName?: string;
  recipeIntro?: string;
  recipeSections?: RecipeSection[];
  recipeVariants?: RecipeVariant[];
  intro?: string;
  ingredients?: IngredientRow[];
  steps?: Array<StepRow | string>;
  difficulty?: string;
  tags?: string[];
  mealPlanLabel?: string;
  confirmedIngredients?: string[];
  dishItems?: DishItem[];
}

type MealPlan = "today_lunch" | "today_dinner" | "week";

interface IngredientDraft {
  imagePath: string;
  imageName: string;
  ingredients: string[];
  mealPlan: MealPlan;
  householdSize: number;
  newIngredient: string;
}

type HistoryTag = "recipe" | "culture" | "stat" | "general";

interface HistoryItem {
  id: string;
  title: string;
  tag: HistoryTag;
  updatedAt: number;
  sessionId: string;
  messages: ChatMessage[];
  startedAt: string;
}

const STORAGE_KEY = "chushen_chat_history_v1";
const LEGACY_STORAGE_KEYS = ["shidian_chat_history_v1", "gustobot_chat_history_v1"];
const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]);
const FILE_EXTENSIONS = new Set([
  ".txt", ".md", ".json", ".csv", ".log", ".xlsx", ".xls", ".pdf", ".doc", ".docx"
]);

type AttachmentKind = "" | "file" | "image";

const state = reactive({
  isTyping: false,
  sessionId: "",
  userInput: "",
  messages: [] as ChatMessage[],
  uploadStatus: "",
  attachedFilePath: "",
  attachedFileName: "",
  attachedKind: "" as AttachmentKind,
  activeHistoryId: "",
  conversationStartedAt: ""
});

const messageContainer = ref<HTMLElement | null>(null);
const ingredientDraft = ref<IngredientDraft | null>(null);

const mealPlanOptions: Array<{ value: MealPlan; label: string }> = [
  { value: "today_lunch", label: "今日午餐" },
  { value: "today_dinner", label: "今日晚餐" },
  { value: "week", label: "一周菜谱" }
];
const historyList = ref<HistoryItem[]>([]);
const userProfile = ref<ChushenProfile>(loadProfile());
const mainView = ref<"chat" | "kitchen">("chat");

const expiryAlerts = computed(() => getExpiryAlerts(userProfile.value, 2));

function updateProfile(next: ChushenProfile) {
  userProfile.value = next;
  saveProfile(next);
}

function chatExtras(): Record<string, unknown> {
  return {
    user_id: userProfile.value.deviceId,
    dietary_profile: profileForApi(userProfile.value)
  };
}

function startPlanFromFridge(ingredients: string[]) {
  if (!ingredients.length || state.isTyping) return;
  mainView.value = "chat";
  ingredientDraft.value = {
    imagePath: "",
    imageName: "虚拟冰箱",
    ingredients: [...ingredients],
    mealPlan: userProfile.value.household.defaultMealPlan,
    householdSize: userProfile.value.household.size,
    newIngredient: ""
  };
  state.uploadStatus = "已从虚拟冰箱载入食材，请确认后推荐菜谱";
}

const isTyping = computed(() => state.isTyping);
const messages = computed(() => state.messages);
const uploadStatus = computed(() => state.uploadStatus);
const userInput = computed({
  get: () => state.userInput,
  set: (val: string) => {
    state.userInput = val;
  }
});
const conversationStartedAt = computed(() => state.conversationStartedAt);

const chatTitle = computed(() => {
  const firstUser = state.messages.find((m) => m.role === "user");
  if (firstUser) return truncate(firstUser.content, 18);
  return "新对话";
});

const lastRoute = computed(() => {
  for (let i = state.messages.length - 1; i >= 0; i -= 1) {
    const m = state.messages[i];
    if (m.role === "assistant" && m.route) return m.route;
  }
  return null;
});

const currentAgentBadge = computed(() => agentBadgeForRoute(lastRoute.value));

const historyGroups = computed(() => {
  const todayStart = startOfDay(Date.now());
  const yesterdayStart = todayStart - 86400000;
  const today: HistoryItem[] = [];
  const yesterday: HistoryItem[] = [];
  const earlier: HistoryItem[] = [];

  for (const item of historyList.value) {
    if (item.updatedAt >= todayStart) today.push(item);
    else if (item.updatedAt >= yesterdayStart) yesterday.push(item);
    else earlier.push(item);
  }

  return [
    { label: "今天", items: today },
    { label: "昨天", items: yesterday },
    { label: "更早", items: earlier }
  ].filter((g) => g.items.length > 0);
});

const followUpSuggestions = computed(() => {
  const route = lastRoute.value;
  if (route === "graphrag-query") {
    return ["需要哪些辅料？", "有没有更简单的做法？", "和类似菜有什么区别？"];
  }
  if (route === "kb-query") {
    return ["还有哪些相关典故？", "这种饮食习俗从哪来？", "同一时期还有什么名菜？"];
  }
  if (route === "text2sql-query") {
    return ["哪个菜系数量最多？", "统计一下麻辣口味有多少？", "各口味分布如何？"];
  }
  return ["香肠炒菜干怎么做", "佛跳墙的历史典故", "数据库里有多少道菜"];
});

const inputPlaceholder = computed(() => {
  if (ingredientDraft.value) return "确认上方食材后点击「确认并推荐菜谱」…";
  if (state.attachedKind === "image") return "例如：图上这道菜怎么做？有哪些食材？";
  if (state.attachedKind === "file") return "针对已上传文件提问…";
  return "问做法、查典故、上传照片提问…";
});

const featurePills = [
  { label: "经典菜谱推荐", icon: "ti ti-heart", prompt: "请推荐几道经典鲁菜，并说明特色。" },
  { label: "一周食谱规划", icon: "ti ti-calendar", prompt: "帮我规划一周的家常晚餐菜单，偏清淡。" },
  { label: "数据统计查询", icon: "ti ti-chart-bar", prompt: "数据库里有多少道菜？哪个口味最多？" },
  { label: "饮食文化探索", icon: "ti ti-book", prompt: "蔬菜是什么时候传入中国的？" }
];

function truncate(text: string, max: number): string {
  const t = text.trim();
  return t.length > max ? `${t.slice(0, max)}…` : t;
}

function startOfDay(ts: number): number {
  const d = new Date(ts);
  d.setHours(0, 0, 0, 0);
  return d.getTime();
}

function formatTimeLabel(date = new Date()): string {
  return `今天 ${date.getHours().toString().padStart(2, "0")}:${date.getMinutes().toString().padStart(2, "0")}`;
}

function routeToTag(route?: string | null): HistoryTag {
  if (route === "graphrag-query" || route === "image-query" || route === "file-query") return "recipe";
  if (route === "kb-query") return "culture";
  if (route === "text2sql-query") return "stat";
  return "general";
}

function tagClass(tag: HistoryTag): string {
  return {
    recipe: "htag-recipe",
    culture: "htag-culture",
    stat: "htag-stat",
    general: "htag-general"
  }[tag];
}

function tagLabel(tag: HistoryTag): string {
  return { recipe: "菜谱", culture: "典故", stat: "统计", general: "对话" }[tag];
}

function routeLabel(route: string): string {
  const map: Record<string, string> = {
    "general-query": "闲聊",
    "additional-query": "追问澄清",
    "kb-query": "文化知识库",
    "graphrag-query": "菜谱图谱",
    "text2sql-query": "数据统计",
    "image-query": "图片识菜",
    "file-query": "文件分析"
  };
  return map[route] || route;
}

function agentBadgeForRoute(route?: string | null) {
  if (!route) return null;
  if (route === "kb-query") {
    return { label: "文化 Agent", icon: "ti ti-book", cls: "agent-badge-c" };
  }
  if (route === "graphrag-query" || route === "image-query") {
    return { label: "菜谱 Agent", icon: "ti ti-tools-kitchen-2", cls: "" };
  }
  if (route === "text2sql-query") {
    return { label: "数据 Agent", icon: "ti ti-chart-bar", cls: "agent-badge-s" };
  }
  return { label: "智能路由", icon: "ti ti-git-branch", cls: "" };
}

function loadHistoryFromStorage() {
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
    historyList.value = raw ? (JSON.parse(raw) as HistoryItem[]) : [];
  } catch {
    historyList.value = [];
  }
}

function persistHistory() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(historyList.value.slice(0, 30)));
}

function upsertCurrentHistory() {
  if (!state.messages.length) return;

  const firstUser = state.messages.find((m) => m.role === "user");
  const lastAssistant = [...state.messages].reverse().find((m) => m.role === "assistant");
  const tag = routeToTag(lastAssistant?.route);
  const title = truncate(firstUser?.content || "新对话", 16);
  const now = Date.now();

  const payload: HistoryItem = {
    id: state.activeHistoryId || crypto.randomUUID(),
    title,
    tag,
    updatedAt: now,
    sessionId: state.sessionId,
    messages: JSON.parse(JSON.stringify(state.messages)),
    startedAt: state.conversationStartedAt || formatTimeLabel()
  };

  const idx = historyList.value.findIndex((h) => h.id === payload.id);
  if (idx >= 0) historyList.value[idx] = payload;
  else historyList.value.unshift(payload);

  state.activeHistoryId = payload.id;
  persistHistory();
}

function loadHistory(id: string) {
  const item = historyList.value.find((h) => h.id === id);
  if (!item) return;
  mainView.value = "chat";
  state.activeHistoryId = item.id;
  state.sessionId = item.sessionId;
  state.messages = JSON.parse(JSON.stringify(item.messages));
  state.conversationStartedAt = item.startedAt;
  clearAttachment();
  clearIngredientDraft();
}

function resetCurrentChat() {
  state.sessionId = "";
  state.messages = [];
  state.activeHistoryId = "";
  state.conversationStartedAt = "";
  clearAttachment();
  clearIngredientDraft();
}

function deleteHistory(id: string) {
  const wasActive = state.activeHistoryId === id;
  historyList.value = historyList.value.filter((h) => h.id !== id);
  persistHistory();
  if (wasActive) resetCurrentChat();
}

function clearAllHistory() {
  if (!historyList.value.length) return;
  if (!window.confirm("确定清空全部对话记录吗？此操作不可恢复。")) return;
  historyList.value = [];
  persistHistory();
  resetCurrentChat();
}

function startNewChat() {
  upsertCurrentHistory();
  resetCurrentChat();
  mainView.value = "chat";
}

function dishesPerMeal(size: number): number {
  if (size <= 2) return 1;
  if (size <= 4) return 2;
  return 3;
}

function adjustHousehold(delta: number) {
  if (!ingredientDraft.value) return;
  ingredientDraft.value.householdSize = Math.min(12, Math.max(1, ingredientDraft.value.householdSize + delta));
}

function mealPlanLabel(plan: MealPlan): string {
  return mealPlanOptions.find((opt) => opt.value === plan)?.label || "今日晚餐";
}

function clearIngredientDraft() {
  ingredientDraft.value = null;
}

function removeIngredient(index: number) {
  if (!ingredientDraft.value) return;
  ingredientDraft.value.ingredients.splice(index, 1);
}

function addIngredient() {
  if (!ingredientDraft.value) return;
  const name = ingredientDraft.value.newIngredient.trim();
  if (!name) return;
  if (!ingredientDraft.value.ingredients.includes(name)) {
    ingredientDraft.value.ingredients.push(name);
  }
  ingredientDraft.value.newIngredient = "";
}

async function startIngredientRecognition() {
  if (state.attachedKind !== "image" || !state.attachedFilePath) return;
  const filePath = state.attachedFilePath;
  const fileName = state.attachedFileName || "图片";
  clearAttachment();
  await recognizeIngredientsFromImage(filePath, fileName);
}

async function recognizeIngredientsFromImage(filePath: string, fileName: string) {
  state.uploadStatus = "正在识别食材…";
  try {
    const { data } = await axios.post(`${API_BASE}/api/v1/vision/ingredients`, {
      image_path: filePath
    });
    const ingredients = Array.isArray(data?.ingredients) ? data.ingredients : [];
    if (!ingredients.length) {
      state.uploadStatus = "未识别到食材，请换一张更清晰的图片。";
      return;
    }
    ingredientDraft.value = {
      imagePath: filePath,
      imageName: fileName,
      ingredients,
      mealPlan: userProfile.value.household.defaultMealPlan,
      householdSize: userProfile.value.household.size,
      newIngredient: ""
    };
    state.uploadStatus = `已识别 ${ingredients.length} 种食材，请确认后推荐菜谱`;
  } catch (error: unknown) {
    state.uploadStatus = getUploadErrorMessage(error);
    clearIngredientDraft();
  }
}

async function confirmIngredients() {
  const draft = ingredientDraft.value;
  if (!draft?.ingredients.length || state.isTyping) return;

  if (!state.conversationStartedAt) {
    state.conversationStartedAt = formatTimeLabel();
  }

  const displayMsg = `已确认食材：${draft.ingredients.join("、")} · ${mealPlanLabel(draft.mealPlan)} · ${draft.householdSize}人用餐 · 请推荐菜谱`;
  state.messages.push({ role: "user", content: displayMsg, hasImage: true });
  clearIngredientDraft();
  state.uploadStatus = "";
  state.isTyping = true;

  updateProfile(upsertFridgeItems(userProfile.value, draft.ingredients, "vision"));

  try {
    const { data } = await axios.post(`${API_BASE}/api/v1/chat`, {
      message: "请根据确认的食材推荐菜谱",
      session_id: state.sessionId || undefined,
      confirmed_ingredients: draft.ingredients,
      meal_plan: draft.mealPlan,
      household_size: draft.householdSize,
      stream: false,
      ...chatExtras()
    });

    if (data?.message) {
      const assistant = enrichAssistantMessage(
        data.message,
        data.route,
        displayMsg,
        draft.ingredients,
        draft.mealPlan
      );
      assistant.routeLogic = data.route_logic || null;
      assistant.sources = data.sources || [];
      state.messages.push(assistant);
    } else {
      state.messages.push({ role: "assistant", content: "抱歉，未能获取到有效的响应。" });
    }

    if (data?.session_id) state.sessionId = data.session_id;
    upsertCurrentHistory();
  } catch (error: unknown) {
    console.error("Ingredient meal plan request failed", error);
    state.messages.push({ role: "assistant", content: "请求出错了，请稍后重试。" });
  } finally {
    state.isTyping = false;
  }
}

function openChat() {
  /* 兼容 App.vue 旧接口 */
}

defineExpose({ openChat, startNewChat });

function getFileExtension(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot >= 0 ? name.slice(dot).toLowerCase() : "";
}

function resolveAttachmentKind(file: File): AttachmentKind {
  const ext = getFileExtension(file.name);
  if (IMAGE_EXTENSIONS.has(ext)) return "image";
  if (FILE_EXTENSIONS.has(ext)) return "file";
  if (file.type.startsWith("image/")) return "image";
  return "";
}

function getUploadErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  return "上传失败，请重试";
}

function clearAttachment() {
  state.attachedFilePath = "";
  state.attachedFileName = "";
  state.attachedKind = "";
  state.uploadStatus = "";
}

function hasStructuredRecipe(message: ChatMessage): boolean {
  const hasBlocks = Boolean(
    message.ingredients?.length ||
      message.steps?.length ||
      message.recipeSections?.length ||
      message.recipeVariants?.length
  );
  if (!hasBlocks) return false;
  return recipeHasCookingSteps({
    steps: message.steps,
    sections: message.recipeSections,
    variants: message.recipeVariants
  });
}

function openKitchen() {
  mainView.value = "kitchen";
}

function flattenMealPlanDishes(items: DishItem[]): Array<{ mealLabel: string; name: string }> {
  const result: Array<{ mealLabel: string; name: string }> = [];
  for (const item of items) {
    const names = dishNamesForItem(item);
    if (names.length) {
      for (const name of names) {
        result.push({ mealLabel: item.title, name });
      }
    } else if (item.body?.trim()) {
      result.push({ mealLabel: item.title, name: item.body.trim().slice(0, 16) });
    }
  }
  return result;
}

function dishNamesForItem(dish: DishItem): string[] {
  if (dish.dishNames?.length) return dish.dishNames;
  return extractDishNamesFromText(dish.body);
}

function parseMealPlanContent(content: string): { dishItems: DishItem[]; scopeLabel: string } {
  const scopeMatch =
    content.match(/##\s*一周食谱[（(](\d+)人[）)]/) ||
    content.match(/【规划范围】([^\n]+)/) ||
    content.match(/##\s*(今日[^\n]+)/);
  const scopeLabel = scopeMatch?.[1]?.trim() || "菜谱推荐";

  const dishItems: DishItem[] = [];

  // 周一 … 周日 + 午餐/晚餐
  const dayPattern = /###\s*(周[一二三四五六日]|星期[一二三四五六日])\s*\n([\s\S]*?)(?=\n###\s*周|\n##\s|$)/g;
  let dayMatch: RegExpExecArray | null;
  while ((dayMatch = dayPattern.exec(content)) !== null) {
    const day = dayMatch[1];
    const block = dayMatch[2];
    const mealPattern = /[-*•]\s*\*\*(午餐|晚餐)\*\*[：:]\s*([^\n]+)/g;
    let mealMatch: RegExpExecArray | null;
    while ((mealMatch = mealPattern.exec(block)) !== null) {
      const body = mealMatch[2].trim();
      dishItems.push({
        title: `${day} · ${mealMatch[1]}`,
        body,
        dishNames: extractDishNamesFromText(body)
      });
    }
  }

  // 单餐推荐：## 今日晚餐（2人） + 1. **菜名**
  if (!dishItems.length) {
    const singleSections = [...content.matchAll(/##\s*([^\n]+)\n([\s\S]*?)(?=\n##\s|$)/g)];
    for (const sec of singleSections) {
      const sectionTitle = sec[1].trim();
      if (/采购提醒|说明/.test(sectionTitle)) continue;
      const block = sec[2];
      const numbered = [
        ...block.matchAll(/(\d+)\.\s*\*\*([^*]+)\*\*([\s\S]*?)(?=\n\d+\.\s*\*\*|$)/g)
      ];
      if (numbered.length) {
        for (const m of numbered) {
          const name = m[2].trim();
          const names = extractDishNamesFromText(name);
          dishItems.push({
            title: sectionTitle,
            body: m[0].trim(),
            dishNames: names.length ? names : extractDishNamesFromText(m[0])
          });
        }
      } else {
        const names = extractDishNamesFromText(block);
        if (names.length) {
          for (const name of names) {
            dishItems.push({ title: sectionTitle, body: name, dishNames: [name] });
          }
        }
      }
    }
  }

  if (!dishItems.length) {
    const sectionPattern = /###\s*([^\n]+)\n([\s\S]*?)(?=\n###\s|$)/g;
    let match: RegExpExecArray | null;
    while ((match = sectionPattern.exec(content)) !== null) {
      const title = match[1].trim();
      const body = match[2].trim();
      if (title && body && !/采购提醒|说明/.test(title)) {
        dishItems.push({ title, body, dishNames: extractDishNamesFromText(body) });
      }
    }
  }

  if (!dishItems.length) {
    const fallbackNames = extractDishNamesFromText(content);
    for (const name of fallbackNames) {
      dishItems.push({ title: scopeLabel, body: name, dishNames: [name] });
    }
  }

  return { dishItems: dishItems.slice(0, 21), scopeLabel };
}

function enrichAssistantMessage(
  content: string,
  route: string | null | undefined,
  userQuestion: string,
  confirmedIngredients?: string[],
  mealPlan?: MealPlan
): ChatMessage {
  const base: ChatMessage = {
    role: "assistant",
    content,
    route: route || null
  };

  if (route === "kb-query") {
    return {
      ...base,
      cardType: "culture",
      cardTitle: truncate(userQuestion.replace(/[？?]/g, ""), 20),
      cardBody: content,
      tags: extractTags(content)
    };
  }

  if (route === "graphrag-query" || route === "image-query") {
    if (/抱歉|无法查看|失败|未配置|找不到/.test(content)) {
      return { ...base, cardType: null };
    }

    const isMealPlanRequest =
      Boolean(confirmedIngredients?.length) ||
      userQuestion.includes("已确认食材") ||
      userQuestion.includes("一周菜谱") ||
      mealPlan === "week" ||
      mealPlan === "today_lunch" ||
      mealPlan === "today_dinner";

    if (route === "graphrag-query" && isMealPlanRequest) {
      const parsed = parseMealPlanContent(content);
      const ingredientsFromUser =
        confirmedIngredients ||
        (userQuestion.match(/已确认食材：([^·]+)/)?.[1]?.split(/[、,，]/).map((s) => s.trim()).filter(Boolean) ?? []);
      const peopleMatch = userQuestion.match(/(\d+)人用餐/);
      const scopeTitle =
        mealPlan === "week"
          ? `一周食谱${peopleMatch ? `（${peopleMatch[1]}人）` : ""}`
          : parsed.scopeLabel;
      return {
        ...base,
        cardType: "meal_plan",
        cardTitle: scopeTitle,
        cardBody: content,
        mealPlanLabel: mealPlan ? mealPlanLabel(mealPlan) : parsed.scopeLabel,
        confirmedIngredients: ingredientsFromUser,
        dishItems: parsed.dishItems
      };
    }

    const parsed = parseRecipeContent(content, userQuestion);
    const dishName = resolveDishNameForCard(userQuestion, parsed.cardTitle, content);
    const structured = Boolean(
      parsed.ingredients.length ||
        parsed.steps.length ||
        parsed.sections.length ||
        parsed.variants.length
    );

    if (structured || dishName) {
      return {
        ...base,
        cardType: "recipe",
        cardTitle: dishName || parsed.cardTitle,
        dishName: dishName || undefined,
        recipeIntro: parsed.intro || undefined,
        ingredients: parsed.ingredients.slice(0, 12),
        steps: parsed.steps.slice(0, 10),
        recipeSections: parsed.sections,
        recipeVariants: parsed.variants,
        difficulty: "图谱检索",
        intro: structured ? "已从菜谱知识图谱整理如下：" : undefined
      };
    }
    return {
      ...base,
      cardType: "recipe",
      cardTitle: parsed.cardTitle,
      dishName: dishName || undefined,
      difficulty: "图谱检索"
    };
  }

  return base;
}

function extractTags(text: string): string[] {
  const tags: string[] = [];
  const keywords = ["北宋", "南宋", "唐代", "清代", "川菜", "粤菜", "杭帮菜", "传入", "典故", "起源"];
  for (const kw of keywords) {
    if (text.includes(kw)) tags.push(kw);
  }
  return tags.slice(0, 4);
}

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  const kind = resolveAttachmentKind(file);
  if (!kind) {
    state.uploadStatus = "不支持的格式";
    input.value = "";
    return;
  }

  state.uploadStatus = kind === "image" ? "正在上传图片…" : "正在上传文件…";
  try {
    const formData = new FormData();
    const endpoint = kind === "image" ? "/api/v1/upload/image" : "/api/v1/upload/file";
    formData.append(kind === "image" ? "image" : "file", file);

    const { data } = await axios.post(`${API_BASE}${endpoint}`, formData, {
      headers: { "Content-Type": "multipart/form-data" }
    });

    if (data?.success) {
      if (kind === "image") {
        state.attachedFilePath = data.file_path;
        state.attachedFileName = data.original_name || file.name;
        state.attachedKind = kind;
        state.uploadStatus = "图片已就绪：可直接提问，或点击「识食材推荐菜谱」";
      } else {
        state.attachedFilePath = data.file_path;
        state.attachedFileName = data.original_name || file.name;
        state.attachedKind = kind;
        state.uploadStatus = `文件已就绪：${state.attachedFileName}`;
      }
    } else {
      throw new Error(data?.detail || "上传失败");
    }
  } catch (error: unknown) {
    state.uploadStatus = getUploadErrorMessage(error);
    clearAttachment();
  } finally {
    input.value = "";
  }
}

function sendSuggestion(prompt: string) {
  if (state.isTyping) return;
  state.userInput = prompt;
  void sendMessage();
}

async function sendMessage() {
  const hasImage = Boolean(state.attachedKind === "image" && state.attachedFilePath);
  const hasFile = Boolean(state.attachedKind === "file" && state.attachedFilePath);
  let message = state.userInput.trim();

  if (!message && hasImage) {
    message = "请看看这张图片，回答我的问题。";
  } else if (!message && hasFile) {
    message = "请分析我上传的文件内容。";
  }

  if (!message || state.isTyping) return;

  const imagePath = hasImage ? state.attachedFilePath : "";
  const filePath = hasFile ? state.attachedFilePath : "";

  if (!state.conversationStartedAt) {
    state.conversationStartedAt = formatTimeLabel();
  }

  state.messages.push({ role: "user", content: message, hasImage });
  state.userInput = "";
  state.isTyping = true;

  try {
    const payload: Record<string, unknown> = {
      message,
      session_id: state.sessionId || undefined,
      stream: false,
      ...chatExtras()
    };

    if (imagePath) payload.image_path = imagePath;
    else if (filePath) {
      payload.file_path = filePath;
      payload.ingest_incremental = true;
    }

    const { data } = await axios.post(`${API_BASE}/api/v1/chat`, payload);

    if (data?.message) {
      const assistant = enrichAssistantMessage(
        data.message,
        data.route,
        message
      );
      assistant.routeLogic = data.route_logic || null;
      assistant.sources = data.sources || [];
      state.messages.push(assistant);
    } else {
      state.messages.push({ role: "assistant", content: "抱歉，未能获取到有效的响应。" });
    }

    if (data?.session_id) state.sessionId = data.session_id;
    clearAttachment();
    upsertCurrentHistory();
  } catch (error: unknown) {
    console.error("Chat request failed", error);
    state.messages.push({ role: "assistant", content: "请求出错了，请稍后重试。" });
  } finally {
    state.isTyping = false;
  }
}

function linkify(text: string): string {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\n/g, "<br>");
}

function formatSource(source: Record<string, unknown>): string {
  const name = source.name || source.title || source.document_id || source.source || source.id;
  return truncate(String(name || "来源"), 22);
}

watch(
  () => state.messages.length,
  async () => {
    await nextTick();
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  }
);

onMounted(() => {
  loadHistoryFromStorage();
  userProfile.value = loadProfile();
});
</script>
