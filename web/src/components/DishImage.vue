<template>
  <div class="dish-image-wrap" :class="{ compact }">
    <div v-if="loading" class="dish-image-placeholder">
      <i class="ti ti-photo" aria-hidden="true"></i>
      <span>加载菜品图…</span>
    </div>
    <div v-else-if="failed || !imageUrl" class="dish-image-placeholder muted">
      <i class="ti ti-photo-off" aria-hidden="true"></i>
      <span>暂无图片</span>
    </div>
    <template v-else>
      <img :src="imageUrl" :alt="`${displayName} 示意图`" class="dish-image" loading="lazy" />
      <span class="dish-image-badge">AI 示意</span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { fetchDishImageUrl, sanitizeDishName } from "../utils/videoSearch";

const props = withDefaults(
  defineProps<{
    dishName: string;
    compact?: boolean;
  }>(),
  { compact: false }
);

const loading = ref(true);
const failed = ref(false);
const imageUrl = ref("");
const displayName = ref("");

async function loadImage(name: string) {
  const clean = sanitizeDishName(name);
  displayName.value = clean;
  loading.value = true;
  failed.value = false;
  imageUrl.value = "";
  if (!clean) {
    loading.value = false;
    failed.value = true;
    return;
  }
  try {
    const url = await fetchDishImageUrl(clean);
    if (url) {
      imageUrl.value = url;
    } else {
      failed.value = true;
    }
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadImage(props.dishName);
});

watch(
  () => props.dishName,
  (name) => {
    void loadImage(name);
  }
);
</script>

<style scoped lang="scss">
.dish-image-wrap {
  position: relative;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-background-secondary, #f7f6f4);
  margin-bottom: 10px;

  &.compact {
    width: 88px;
    height: 66px;
    flex-shrink: 0;
    margin-bottom: 0;
  }
}

.dish-image {
  display: block;
  width: 100%;
  height: auto;
  max-height: 180px;
  object-fit: cover;

  .compact & {
    width: 100%;
    height: 100%;
    max-height: none;
  }
}

.dish-image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 120px;
  color: var(--color-text-tertiary, #a8a29e);
  font-size: 11px;

  .compact & {
    min-height: 66px;
    font-size: 10px;
  }

  &.muted {
    opacity: 0.75;
  }

  i {
    font-size: 18px;
  }
}

.dish-image-badge {
  position: absolute;
  right: 6px;
  bottom: 6px;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
}
</style>
