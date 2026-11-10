<template>
  <div class="pantry-page">
    <!-- Orea 式大数字概览卡 -->
    <div class="overview-card orea-card">
      <div class="ov-main">
        <div class="ov-num">{{ activeCount }}<span class="ov-unit"> 种</span></div>
        <div class="ov-label">在库食材 · 估算总重 {{ totalWeightText }}</div>
      </div>
      <div class="ov-metrics">
        <div class="ov-metric">
          <span class="ring" style="border-color: var(--c-green)"></span>
          <div><b>{{ activeCount }}</b><small>在库</small></div>
        </div>
        <div class="ov-metric">
          <span class="ring" style="border-color: var(--c-blue)"></span>
          <div><b>{{ consumedCount }}</b><small>已消耗</small></div>
        </div>
        <div class="ov-metric">
          <span class="ring" style="border-color: var(--c-orange)"></span>
          <div><b>{{ totalWeightText }}</b><small>总重量估算</small></div>
        </div>
      </div>
      <div class="ov-tip">✨ {{ tipText }}</div>
    </div>

    <!-- 顶部操作 -->
    <header class="pantry-head">
      <div>
        <h1 class="page-title">我的库存</h1>
        <p class="page-sub">单位按平均大小自动折算重量</p>
      </div>
      <div class="head-actions">
        <el-switch v-model="showConsumed" active-text="显示已消耗" @change="load" />
        <el-button type="primary" round @click="openAdd">
          <el-icon style="margin-right:4px"><Plus /></el-icon>添加食材
        </el-button>
      </div>
    </header>

    <!-- 骨架屏 -->
    <div v-if="loading" class="list">
      <div v-for="i in 4" :key="'sk' + i" class="food-row orea-card sk-row">
        <div class="sk-tile"></div>
        <div style="flex:1">
          <div class="sk-bar w50"></div>
          <div class="sk-bar w30"></div>
        </div>
      </div>
    </div>

    <!-- 食材行卡 -->
    <div v-else-if="items.length" class="list">
      <div v-for="it in items" :key="it.id" class="food-row orea-card" :class="{ consumed: it.consumed }">
        <div class="food-tile">
          <img v-if="match(it.name).img" :src="match(it.name).img" :alt="it.name"
               loading="lazy" @error="($event.target.style.display='none')" />
          <span v-else class="tile-fallback">{{ match(it.name).emoji }}</span>
        </div>
        <div class="food-info">
          <div class="food-name">{{ it.name }}</div>
          <div class="food-qty">
            {{ fmtQty(it.quantity) }} {{ it.unit || '' }}
            <em v-if="estimate(it)">{{ estimate(it) }}</em>
            <template v-if="it.note"> · {{ it.note }}</template>
          </div>
        </div>
        <span class="state-pill" :class="it.consumed ? 'off' : 'on'">
          <span class="dot"></span>{{ it.consumed ? '已消耗' : '在库' }}
        </span>
        <div class="food-actions">
          <el-tooltip content="改数量" placement="top">
            <button class="act" @click="quickEdit(it)">✏️</button>
          </el-tooltip>
          <el-tooltip :content="it.consumed ? '恢复在库' : '标记消耗'" placement="top">
            <button class="act" @click="toggleConsumed(it)">{{ it.consumed ? '↩️' : '✅' }}</button>
          </el-tooltip>
          <el-tooltip content="删除" placement="top">
            <button class="act del" @click="remove(it)">🗑️</button>
          </el-tooltip>
        </div>
      </div>
    </div>
    <div v-else class="orea-card empty-card">
      <el-empty description="冰箱空空如也，添加点食材吧" :image-size="90" />
    </div>

    <!-- 添加弹窗 -->
    <el-dialog v-model="dialog" title="添加食材" width="440px">
      <div v-if="preview" class="preview-card">
        <div class="preview-img">
          <img v-if="preview.img" :src="preview.img" @error="preview.img = null" />
          <span v-else>{{ preview.emoji }}</span>
        </div>
        <div class="preview-meta">
          <b>{{ preview.name }}</b>
          <small>{{ preview.cat }}</small>
          <small v-if="preview.avg && COUNT_UNITS.includes(preview.unit)">
            按平均大小：1 {{ preview.unit }} ≈ {{ preview.avg }}g
          </small>
          <small v-else-if="COUNT_UNITS.includes(preview.unit)">该食材无平均重量，请用 g / kg 记录</small>
          <small v-else>按 {{ preview.unit }} 精确计量</small>
        </div>
      </div>

      <el-form label-width="62px">
        <el-form-item label="名称">
          <el-autocomplete
            v-model="form.name"
            :fetch-suggestions="queryIngredients"
            value-key="name"
            placeholder="输入食材名，如 番茄 / 鸡蛋 / 鲈鱼"
            popper-class="ing-popper"
            clearable
            style="width: 100%"
            @input="onNameInput"
            @select="onPickIngredient"
          >
            <template #default="{ item }">
              <div class="ing-sug">
                <img v-if="item.img" :src="item.img" class="ing-sug-img" loading="lazy" />
                <span v-else class="ing-sug-img ing-sug-ph">{{ item.emoji }}</span>
                <div class="ing-sug-meta">
                  <b>{{ item.name }}</b>
                  <small>{{ item.cat }}<template v-if="item.unit && item.unit !== 'g'"> · 常用单位 {{ item.unit }}</template></small>
                </div>
              </div>
            </template>
          </el-autocomplete>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.quantity" :min="0" :step="UNIT_STEP[form.unit] || 1" />
          <span v-if="formWeight" class="weight-hint">≈ {{ formWeight }}</span>
        </el-form-item>
        <el-form-item label="单位">
          <el-select v-model="form.unit" placeholder="选择单位" style="width: 160px"
                     filterable allow-create default-first-option>
            <el-option v-for="u in UNIT_OPTIONS" :key="u" :label="u" :value="u" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" placeholder="可选，如：冷藏、周三到期" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="dialog = false">取消</el-button>
        <el-button type="primary" round @click="add">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, errMsg } from '../api'
import { INGREDIENTS, UNIT_OPTIONS, COUNT_UNITS, UNIT_STEP, matchIngredient, toGrams, fmtWeight } from '../data/ingredients'

const items = ref([])
const showConsumed = ref(false)
const loading = ref(true)
const dialog = ref(false)
const form = reactive({ name: '', quantity: 1, unit: '个', note: '' })
const preview = ref(null)

const activeItems = computed(() => items.value.filter((i) => !i.consumed))
const activeCount = computed(() => activeItems.value.length)
const consumedCount = computed(() => items.value.length - activeCount.value)
const notedCount = computed(() => items.value.filter((i) => i.note).length)

const totalWeightText = computed(() => {
  let g = 0
  for (const it of activeItems.value) {
    const v = toGrams(it.name, it.quantity, it.unit)
    if (v) g += v
  }
  return g ? fmtWeight(g) : '—'
})

const tipText = computed(() => {
  const n = activeCount.value
  if (n === 0) return '先添加几样食材，AI 就能帮你想今天吃什么'
  if (n <= 3) return '库存不多啦，正好让 AI 用现有的安排一顿'
  if (n <= 8) return '食材充足，去「AI 对话」问一句今天吃什么吧'
  return '库存丰富，做菜自由度很高，试试让 AI 搭一桌菜单'
})

const formWeight = computed(() => {
  if (!form.name || !form.quantity) return ''
  const g = toGrams(form.name, form.quantity, form.unit)
  return g ? fmtWeight(g) : ''
})

function match(name) { return matchIngredient(name) }

function fmtQty(q) {
  if (q === null || q === undefined) return '—'
  return Number.isInteger(q) ? q : Number(q).toFixed(1)
}

function estimate(it) {
  if (it.unit === '毫升') return it.quantity ? `${Math.round(it.quantity)}ml` : ''
  if (it.unit === 'kg' || it.unit === '斤' || it.unit === 'g') {
    // 已是精确单位，不必再折算
    return ''
  }
  const g = toGrams(it.name, it.quantity, it.unit)
  return g ? `≈ ${fmtWeight(g)}` : ''
}

/** 联想搜索：前缀命中优先，其次包含匹配；空输入时给常用食材 */
function queryIngredients(query, cb) {
  const q = String(query || '').trim()
  const pool = INGREDIENTS.map((it) => ({
    ...it,
    emoji: matchIngredient(it.name).emoji,
  }))
  let list
  if (!q) {
    list = pool.slice(0, 10)
  } else {
    const starts = pool.filter((it) => it.name.startsWith(q))
    const includes = pool.filter((it) => !it.name.startsWith(q) && (it.name.includes(q) || q.includes(it.name)))
    const byCat = pool.filter((it) => !starts.includes(it) && !includes.includes(it) && it.cat.includes(q))
    list = [...starts, ...includes, ...byCat].slice(0, 10)
  }
  cb(list)
}

/** 选中联想项：填名称 + 带出默认单位 + 刷新预览 */
function onPickIngredient(item) {
  form.name = item.name
  if (item.unit && UNIT_OPTIONS.includes(item.unit)) form.unit = item.unit
  preview.value = { ...item, emoji: item.emoji || '🥗' }
}

function onNameInput() {
  const m = matchIngredient(form.name)
  preview.value = m.name ? m : { name: form.name, emoji: '🥗', cat: '未收录', avg: null, unit: 'g', img: null }
  // 名称匹配到图库时，单位自动跟着走（用户可改）
  if (m.name && m.unit && UNIT_OPTIONS.includes(m.unit)) form.unit = m.unit
}

function openAdd() {
  dialog.value = true
  preview.value = null
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.listPantry({ include_consumed: showConsumed.value })
    items.value = data
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function add() {
  if (!form.name.trim()) { ElMessage.warning('请输入食材名'); return }
  try {
    await api.addPantry({
      name: form.name.trim(),
      quantity: form.quantity || null,
      unit: form.unit || null,
      note: form.note || null,
    })
    ElMessage.success('已添加')
    dialog.value = false
    form.name = ''; form.quantity = 1; form.unit = '个'; form.note = ''
    preview.value = null
    load()
  } catch (e) { ElMessage.error(errMsg(e)) }
}

async function quickEdit(row) {
  const { value } = await ElMessageBox.prompt('新的数量', `修改 ${row.name}`, { inputValue: row.quantity ?? 0 })
  const q = parseFloat(value)
  if (Number.isNaN(q)) return
  await api.updatePantry(row.id, { quantity: q })
  load()
}

async function toggleConsumed(row) {
  await api.updatePantry(row.id, { consumed: !row.consumed })
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`删除「${row.name}」？`, '提示', { type: 'warning' })
  await api.deletePantry(row.id)
  load()
}
</script>

<style scoped>
.pantry-page { padding: 24px 32px 32px; max-width: 860px; margin: 0 auto; }

.overview-card { padding: 22px 24px; margin-bottom: 20px; }
.ov-num { font-size: 40px; font-weight: 800; color: var(--ink-900); line-height: 1.1; }
.ov-unit { font-size: 16px; font-weight: 600; color: var(--ink-600); }
.ov-label { font-size: 13px; color: var(--ink-400); margin-top: 6px; }
.ov-metrics { display: flex; gap: 28px; margin-top: 16px; }
.ov-metric { display: flex; align-items: center; gap: 9px; }
.ov-metric b { display: block; font-size: 16px; color: var(--ink-900); line-height: 1.1; }
.ov-metric small { font-size: 11px; color: var(--ink-400); }
.ring { width: 14px; height: 14px; border-radius: 50%; border: 3.5px solid var(--c-green); flex-shrink: 0; }
.ov-tip { margin-top: 16px; padding: 11px 14px; background: var(--brand-50); border-radius: 12px; font-size: 12.5px; color: var(--ink-600); line-height: 1.6; }

.pantry-head { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 14px; margin-bottom: 16px; }
.head-actions { display: flex; gap: 16px; align-items: center; }

.list { display: grid; gap: 10px; }
.food-row { display: flex; align-items: center; gap: 14px; padding: 11px 16px; border-radius: 16px; transition: transform .15s ease; }
.food-row:hover { transform: translateY(-1px); }
.food-row.consumed { opacity: .55; }
.food-row.consumed .food-name { text-decoration: line-through; }

.food-tile {
  width: 52px; height: 52px; border-radius: 14px; flex-shrink: 0;
  background: var(--ink-100); border: 1px solid var(--ink-200); overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.food-tile img { width: 100%; height: 100%; object-fit: cover; display: block; }
.tile-fallback { font-size: 24px; }

.food-info { flex: 1; min-width: 0; }
.food-name { font-size: 14.5px; font-weight: 700; color: var(--ink-900); }
.food-qty { font-size: 12px; color: var(--ink-400); margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.food-qty em { font-style: normal; color: var(--c-green); font-weight: 600; margin-left: 4px; }

.state-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; padding: 3px 10px; border-radius: 999px; font-weight: 600; background: var(--fresh-bg); color: var(--fresh); flex-shrink: 0; }
.state-pill .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--fresh); }
.state-pill.off { background: var(--ink-100); color: var(--ink-400); }
.state-pill.off .dot { background: var(--ink-400); }

.food-actions { display: flex; gap: 10px; opacity: 0; transition: opacity .15s; }
.food-row:hover .food-actions { opacity: 1; }
.act { border: none; background: none; font-size: 15px; cursor: pointer; transition: transform .12s; }
.act:hover { transform: scale(1.2); }

.empty-card { padding: 30px 0; }

.preview-card {
  display: flex; gap: 14px; align-items: center;
  background: var(--ink-100); border-radius: 14px; padding: 12px 14px; margin-bottom: 16px;
}
.preview-img {
  width: 62px; height: 62px; border-radius: 12px; overflow: hidden; flex-shrink: 0;
  background: #fff; border: 1px solid var(--ink-200);
  display: flex; align-items: center; justify-content: center; font-size: 28px;
}
.preview-img img { width: 100%; height: 100%; object-fit: cover; }
.preview-meta b { display: block; font-size: 15px; color: var(--ink-900); margin-bottom: 2px; }
.preview-meta small { display: block; font-size: 11.5px; color: var(--ink-600); line-height: 1.6; }
.weight-hint { margin-left: 12px; font-size: 12px; color: var(--c-green); font-weight: 600; }

/* 联想下拉 */
:deep(.ing-sug) { display: flex; align-items: center; gap: 10px; padding: 4px 0; }
:deep(.ing-sug-img) {
  width: 32px; height: 32px; border-radius: 8px; object-fit: cover;
  background: var(--ink-100); flex-shrink: 0;
}
:deep(.ing-sug-ph) { display: flex; align-items: center; justify-content: center; font-size: 16px; }
:deep(.ing-sug-meta) { display: flex; flex-direction: column; line-height: 1.25; }
:deep(.ing-sug-meta b) { font-size: 13px; color: var(--ink-900); }
:deep(.ing-sug-meta small) { font-size: 11px; color: var(--ink-400); }

/* 骨架 */
.sk-row { pointer-events: none; }
.sk-tile, .sk-bar {
  background: linear-gradient(90deg, #eef2f8 25%, #f7fafd 50%, #eef2f8 75%);
  background-size: 200% 100%;
  animation: shimmerP 1.3s infinite;
}
.sk-tile { width: 52px; height: 52px; border-radius: 14px; flex-shrink: 0; }
.sk-bar { height: 12px; border-radius: 6px; margin-bottom: 8px; }
.sk-bar.w50 { width: 50%; }
.sk-bar.w30 { width: 30%; }
@keyframes shimmerP { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

@media (max-width: 768px) {
  .pantry-page { padding: 16px 14px 24px; }
  .food-actions { opacity: 1; }
  .ov-metrics { gap: 18px; }
}
</style>
