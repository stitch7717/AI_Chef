<template>
  <div class="discover-page">
    <!-- 顶部：标题 + 搜索 -->
    <header class="discover-head">
      <div>
        <h1 class="page-title">发现菜谱</h1>
        <p class="page-sub">像逛展览一样，发现一道好菜</p>
      </div>
      <el-input v-model="keyword" placeholder="搜索菜名…" clearable class="search"
                @keyup.enter="search" @clear="load">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </header>

    <!-- 分类 chips -->
    <div class="cat-row">
      <span class="cat" :class="{ on: mode === 'all' }" @click="switchMode('all')">全部作品</span>
      <span class="cat" :class="{ on: mode === 'fav' }" @click="switchMode('fav')">我的收藏</span>
      <span v-for="c in quickCats" :key="c.kw" class="cat"
            :class="{ on: mode === c.kw }" @click="searchCat(c.kw)">{{ c.label }}</span>
    </div>

    <!-- 首屏骨架屏 -->
    <div v-if="loading" class="masonry">
      <div v-for="i in 6" :key="'sk' + i" class="expo-card sk-card">
        <div class="sk-cover" :style="{ height: (130 + (i % 3) * 25) + 'px' }"></div>
        <div class="sk-body">
          <div class="sk-line w60"></div>
          <div class="sk-line w40"></div>
        </div>
      </div>
    </div>

    <!-- 瀑布流展览卡片 -->
    <div v-else-if="recipes.length" class="masonry">
      <article v-for="(r, i) in recipes" :key="r.id" class="expo-card" @click="showDetail(r)">
        <div class="cover" :class="`cover-${i % 5}`">
          <img v-if="r.image_url" :src="r.image_url" class="cover-img" loading="lazy"
               @error="r.image_url = ''" />
          <span v-else class="cover-art">{{ dishEmoji(r) }}</span>
          <span class="difficulty-pill">{{ r.difficulty }}</span>
          <button class="heart" :class="{ on: isFav(r.id) }" @click.stop="toggleFav(r)">
            {{ isFav(r.id) ? '♥' : '♡' }}
          </button>
        </div>
        <div class="expo-body">
          <h3 class="expo-title">{{ r.name }}</h3>
          <div class="tag-row">
            <span v-for="ing in r.ingredients.slice(0, 3)" :key="ing" class="mini-tag">{{ ing }}</span>
            <span v-if="r.ingredients.length > 3" class="mini-tag more">+{{ r.ingredients.length - 3 }}</span>
          </div>
          <div class="expo-meta">
            <span class="nutrition">💡 {{ shortNutrition(r.nutrition) }}</span>
          </div>
        </div>
      </article>
    </div>

    <el-empty v-else-if="!loading" description="没有找到菜谱" :image-size="100" />

    <!-- 详情：展览画册式弹窗 -->
    <el-dialog v-model="detailVisible" width="560px" class="detail-dialog" :show-close="true">
      <template v-if="detail">
        <div class="detail-cover" :class="`cover-${detail.id % 5}`">
          <img v-if="detail.image_url" :src="detail.image_url" class="cover-img"
               @error="detail.image_url = ''" />
          <span v-else class="detail-art">{{ dishEmoji(detail) }}</span>
          <div class="detail-cover-info">
            <h2>{{ detail.name }}</h2>
            <span class="difficulty-pill">{{ detail.difficulty }}</span>
          </div>
        </div>
        <div class="detail-body">
          <section>
            <h4>🥬 展品清单 · 食材</h4>
            <div class="tag-row">
              <span v-for="ing in detail.ingredients" :key="ing" class="mini-tag lg">{{ ing }}</span>
            </div>
          </section>
          <section>
            <h4>👨‍🍳 导览路线 · 步骤</h4>
            <div class="steps-panel">{{ detail.steps }}</div>
          </section>
          <section>
            <h4>💪 营养看点</h4>
            <p class="nutrition-line">{{ detail.nutrition }}</p>
          </section>
          <el-divider />
          <div class="rate-row">
            <span>吃过这道菜？评个分：</span>
            <el-rate v-model="myRating" />
            <el-button size="small" type="primary" round @click="submitFeedback">提交</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { api, errMsg } from '../api'

const recipes = ref([])
const favIds = ref(new Set())
const mode = ref('all')
const keyword = ref('')
const detail = ref(null)
const detailVisible = ref(false)
const myRating = ref(4)
const loading = ref(true)

const quickCats = [
  { kw: '汤', label: '🍲 暖汤' },
  { kw: '鸡', label: '🍗 家禽' },
  { kw: '鱼', label: '🐟 鲜鱼' },
  { kw: '蛋', label: '🍳 蛋料理' },
  { kw: '沙拉', label: '🥗 轻食' },
]

function dishEmoji(r) {
  const t = `${r.name}${(r.ingredients || []).join('')}`
  if (/鱼|虾|蟹|海鲜/.test(t)) return '🐟'
  if (/牛/.test(t)) return '🥩'
  if (/鸡|鸭/.test(t)) return '🍗'
  if (/汤|煲/.test(t)) return '🍲'
  if (/面|粉/.test(t)) return '🍜'
  if (/粥/.test(t)) return '🥣'
  if (/蛋/.test(t)) return '🍳'
  if (/沙拉|轻食/.test(t)) return '🥗'
  if (/豆腐/.test(t)) return '🥘'
  return '🍽️'
}

function shortNutrition(n) {
  if (!n) return ''
  const s = String(n)
  return s.length > 26 ? s.slice(0, 26) + '…' : s
}

function isFav(id) { return favIds.value.has(id) }

async function load() {
  loading.value = true
  try {
    if (mode.value === 'fav') {
      const { data } = await api.listFavorites()
      recipes.value = data
    } else {
      const { data } = await api.listRecipes({ limit: 200 })
      recipes.value = data
    }
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

async function search() {
  if (!keyword.value.trim()) { mode.value = 'all'; load(); return }
  mode.value = 'search'
  loading.value = true
  try {
    const { data } = await api.searchRecipes(keyword.value.trim())
    recipes.value = data
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

async function searchCat(kw) {
  mode.value = kw
  keyword.value = kw
  loading.value = true
  try {
    const { data } = await api.searchRecipes(kw)
    recipes.value = data
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

function switchMode(m) {
  mode.value = m
  keyword.value = ''
  load()
}

async function loadFavs() {
  const { data } = await api.listFavorites()
  favIds.value = new Set(data.map((r) => r.id))
}

onMounted(async () => { await Promise.all([load(), loadFavs()]) })

function showDetail(r) { detail.value = r; myRating.value = 4; detailVisible.value = true }

async function toggleFav(r) {
  try {
    if (isFav(r.id)) { await api.removeFavorite(r.id); favIds.value.delete(r.id); ElMessage.success('已取消收藏') }
    else { await api.addFavorite(r.id); favIds.value.add(r.id); ElMessage.success('已收藏') }
    if (mode.value === 'fav') load()
  } catch (e) { ElMessage.error(errMsg(e)) }
}

async function submitFeedback() {
  try {
    await api.addFeedback({
      recipe_id: detail.value.id,
      rating: myRating.value,
      cooked: true,
      comment: null,
    })
    ElMessage.success('感谢反馈！推荐会越来越懂你')
    detailVisible.value = false
  } catch (e) { ElMessage.error(errMsg(e)) }
}
</script>

<style scoped>
.discover-page { padding: 28px 32px; max-width: 1080px; margin: 0 auto; }

.discover-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; }
.search { width: 260px; }

/* 分类 chips */
.cat-row { display: flex; gap: 10px; margin: 18px 0 22px; flex-wrap: wrap; }
.cat {
  padding: 8px 18px; border-radius: 999px; font-size: 13px; cursor: pointer;
  background: var(--card); border: 1px solid var(--ink-200); color: var(--ink-600);
  transition: all .15s ease; user-select: none;
}
.cat:hover { border-color: var(--brand-500); color: var(--brand-600); }
.cat.on {
  background: var(--ink-900); border-color: var(--ink-900); color: #fff; font-weight: 600;
}

/* 瀑布流 */
.masonry { column-count: 3; column-gap: 16px; }
.expo-card {
  break-inside: avoid; margin-bottom: 16px;
  background: var(--card); border-radius: 18px; overflow: hidden;
  border: 1px solid var(--ink-100);
  box-shadow: 0 2px 10px rgba(28, 25, 23, .04);
  cursor: pointer; transition: transform .18s ease, box-shadow .18s ease;
}
.expo-card:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(28, 25, 23, .1); }

/* 封面：5 套展览配色轮换 */
.cover { position: relative; display: flex; align-items: center; justify-content: center; }
.cover-0 { background: linear-gradient(140deg, #eaf1ff, #cfe0f8); height: 150px; }
.cover-1 { background: linear-gradient(140deg, #e6f8f1, #c4ecdd); height: 180px; }
.cover-2 { background: linear-gradient(140deg, #ffeceb, #fdd9d6); height: 130px; }
.cover-3 { background: linear-gradient(140deg, #f3efff, #ddd4fb); height: 170px; }
.cover-4 { background: linear-gradient(140deg, #fff4e0, #fbe3b8); height: 145px; }
.cover-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.cover-art { font-size: 46px; filter: drop-shadow(0 4px 8px rgba(27,43,74,.10)); }

.difficulty-pill {
  position: absolute; top: 10px; left: 10px;
  padding: 3px 10px; border-radius: 999px;
  background: rgba(255, 255, 255, .85); backdrop-filter: blur(4px);
  font-size: 11px; font-weight: 700; color: var(--ink-900);
}
.heart {
  position: absolute; top: 8px; right: 10px;
  width: 32px; height: 32px; border-radius: 50%; border: none; cursor: pointer;
  background: rgba(255, 255, 255, .85); backdrop-filter: blur(4px);
  font-size: 16px; color: var(--ink-400);
  display: flex; align-items: center; justify-content: center;
  transition: all .15s ease;
}
.heart:hover { transform: scale(1.12); }
.heart.on { color: var(--brand-600); }

.expo-body { padding: 12px 14px 14px; }
.expo-title { font-size: 15px; font-weight: 700; color: var(--ink-900); margin-bottom: 8px; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; }
.mini-tag {
  font-size: 11px; padding: 2px 9px; border-radius: 999px;
  background: var(--ink-100); color: var(--ink-600);
}
.mini-tag.more { background: var(--brand-50); color: var(--brand-600); }
.mini-tag.lg { font-size: 12px; padding: 4px 12px; }
.expo-meta { margin-top: 10px; }
.nutrition {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--ink-600); font-weight: 600;
  background: var(--ink-100); border-radius: 999px; padding: 4px 10px;
}
.nutrition::before {
  content: ''; width: 8px; height: 8px; border-radius: 50%;
  background: var(--flame);
}

/* ---- 详情弹窗（画册式） ---- */
.detail-cover {
  margin: -12px -12px 0; position: relative;
  display: flex; align-items: center; justify-content: center; height: 180px;
}

.detail-art { font-size: 60px; filter: drop-shadow(0 5px 10px rgba(27,43,74,.10)); }
.detail-cover-info {
  position: absolute; left: 18px; bottom: 14px;
  display: flex; align-items: center; gap: 10px;
}
.detail-cover-info h2 {
  font-size: 22px; font-weight: 800; color: var(--ink-900);
  background: rgba(255,255,255,.85); backdrop-filter: blur(4px);
  padding: 4px 14px; border-radius: 999px;
}
.detail-body { padding: 18px 6px 4px; }
.detail-body section { margin-bottom: 16px; }
h4 { font-size: 13px; color: var(--ink-600); margin-bottom: 8px; font-weight: 700; }
.steps-panel {
  background: var(--surface); border: 1px dashed var(--ink-200); border-radius: 12px;
  padding: 14px 16px; font-size: 13.5px; line-height: 1.9; white-space: pre-wrap;
  color: var(--ink-900);
}
.nutrition-line { font-size: 13px; color: var(--ink-600); }
.rate-row { display: flex; align-items: center; gap: 12px; font-size: 13px; color: var(--ink-600); }

/* 骨架屏 */
.sk-card { pointer-events: none; }
.sk-cover, .sk-line {
  background: linear-gradient(90deg, #eef2f8 25%, #f7fafd 50%, #eef2f8 75%);
  background-size: 200% 100%;
  animation: shimmer 1.3s infinite;
}
.sk-body { padding: 12px 14px 16px; }
.sk-line { height: 12px; border-radius: 6px; margin-bottom: 8px; }
.sk-line.w60 { width: 60%; }
.sk-line.w40 { width: 40%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

@media (max-width: 900px) { .masonry { column-count: 2; } }
@media (max-width: 768px) {
  .discover-page { padding: 16px 14px; }
  .search { width: 100%; }
}
</style>
