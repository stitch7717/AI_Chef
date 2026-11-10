// 食材知识库（前端本地数据，无后端依赖）
// 单位只用精确单位：个 / g / kg / 斤 / 毫升 / 条 / 片
// avg = 该食材「1 个单位」的平均克数（仅 个/条/片 需要，用于折算）

export const INGREDIENTS = [
  { name: '番茄', avg: 200, unit: '个', cat: '蔬菜', img: '/ingredient-images/0.jpg' },
  { name: '土豆', avg: 200, unit: '个', cat: '蔬菜', img: '/ingredient-images/1.jpg' },
  { name: '洋葱', avg: 200, unit: '个', cat: '蔬菜', img: '/ingredient-images/2.jpg' },
  { name: '胡萝卜', avg: 120, unit: '个', cat: '蔬菜', img: '/ingredient-images/3.jpg' },
  { name: '白萝卜', avg: 700, unit: '个', cat: '蔬菜', img: '/ingredient-images/4.jpg' },
  { name: '黄瓜', avg: 200, unit: '个', cat: '蔬菜', img: '/ingredient-images/5.jpg' },
  { name: '茄子', avg: 300, unit: '个', cat: '蔬菜', img: '/ingredient-images/6.jpg' },
  { name: '青椒', avg: 80, unit: '个', cat: '蔬菜', img: '/ingredient-images/7.jpg' },
  { name: '尖椒', avg: 30, unit: '个', cat: '蔬菜', img: '/ingredient-images/8.jpg' },
  { name: '小米椒', avg: 5, unit: '个', cat: '蔬菜', img: '/ingredient-images/9.jpg' },
  { name: '白菜', avg: 1200, unit: '个', cat: '蔬菜', img: '/ingredient-images/10.jpg' },
  { name: '娃娃菜', avg: 300, unit: '个', cat: '蔬菜', img: '/ingredient-images/11.jpg' },
  { name: '包菜', avg: 1000, unit: '个', cat: '蔬菜', img: '/ingredient-images/12.jpg' },
  { name: '生菜', avg: 400, unit: '个', cat: '蔬菜', img: '/ingredient-images/13.jpg' },
  { name: '油菜', avg: 300, unit: '个', cat: '蔬菜', img: '/ingredient-images/14.jpg' },
  { name: '菠菜', avg: 300, unit: '个', cat: '蔬菜', img: '/ingredient-images/15.jpg' },
  { name: '空心菜', avg: 300, unit: '个', cat: '蔬菜', img: '/ingredient-images/16.jpg' },
  { name: '韭菜', avg: 250, unit: '个', cat: '蔬菜', img: '/ingredient-images/17.jpg' },
  { name: '芹菜', avg: 400, unit: '个', cat: '蔬菜', img: '/ingredient-images/18.jpg' },
  { name: '蒜苔', avg: 250, unit: '个', cat: '蔬菜', img: '/ingredient-images/19.jpg' },
  { name: '西兰花', avg: 400, unit: '个', cat: '蔬菜', img: '/ingredient-images/20.jpg' },
  { name: '花菜', avg: 700, unit: '个', cat: '蔬菜', img: '/ingredient-images/21.jpg' },
  { name: '莲藕', avg: 300, unit: '个', cat: '蔬菜', img: '/ingredient-images/22.jpg' },
  { name: '山药', avg: 400, unit: '个', cat: '蔬菜', img: '/ingredient-images/23.jpg' },
  { name: '冬瓜', avg: 2000, unit: '个', cat: '蔬菜', img: '/ingredient-images/24.jpg' },
  { name: '南瓜', avg: 1500, unit: '个', cat: '蔬菜', img: '/ingredient-images/25.jpg' },
  { name: '丝瓜', avg: 250, unit: '个', cat: '蔬菜', img: '/ingredient-images/26.jpg' },
  { name: '苦瓜', avg: 250, unit: '个', cat: '蔬菜', img: '/ingredient-images/27.jpg' },
  { name: '四季豆', avg: 300, unit: '个', cat: '蔬菜', img: '/ingredient-images/28.jpg' },
  { name: '豆角', avg: 300, unit: '个', cat: '蔬菜', img: '/ingredient-images/29.jpg' },
  { name: '豌豆', avg: null, unit: 'g', cat: '蔬菜', img: '/ingredient-images/30.jpg' },
  { name: '玉米', avg: 250, unit: '个', cat: '蔬菜', img: '/ingredient-images/31.jpg' },
  { name: '香菇', avg: 20, unit: '个', cat: '菌菇', img: '/ingredient-images/32.jpg' },
  { name: '口蘑', avg: 15, unit: '个', cat: '菌菇', img: '/ingredient-images/33.jpg' },
  { name: '金针菇', avg: 150, unit: '个', cat: '菌菇', img: '/ingredient-images/34.jpg' },
  { name: '木耳', avg: null, unit: 'g', cat: '菌菇', img: '/ingredient-images/35.jpg' },
  { name: '银耳', avg: 15, unit: '个', cat: '菌菇', img: '/ingredient-images/36.jpg' },
  { name: '海带', avg: 50, unit: '片', cat: '蔬菜', img: '/ingredient-images/37.jpg' },
  { name: '紫菜', avg: null, unit: 'g', cat: '蔬菜', img: '/ingredient-images/38.jpg' },
  { name: '豆腐', avg: 350, unit: '个', cat: '豆制品', img: '/ingredient-images/39.jpg' },
  { name: '豆干', avg: 30, unit: '片', cat: '豆制品', img: '/ingredient-images/40.jpg' },
  { name: '腐竹', avg: null, unit: 'g', cat: '豆制品', img: '/ingredient-images/41.jpg' },
  { name: '粉丝', avg: 100, unit: '个', cat: '主食', img: '/ingredient-images/42.jpg' },
  { name: '粉条', avg: 150, unit: '个', cat: '主食', img: '/ingredient-images/43.jpg' },
  { name: '豆芽', avg: null, unit: 'g', cat: '蔬菜', img: '/ingredient-images/44.jpg' },
  { name: '莴笋', avg: 400, unit: '个', cat: '蔬菜', img: '/ingredient-images/45.jpg' },
  { name: '竹笋', avg: 200, unit: '个', cat: '蔬菜', img: '/ingredient-images/46.jpg' },
  { name: '芦笋', avg: 250, unit: '个', cat: '蔬菜', img: '/ingredient-images/47.jpg' },
  { name: '秋葵', avg: 200, unit: '个', cat: '蔬菜', img: '/ingredient-images/48.jpg' },
  { name: '香葱', avg: 50, unit: '个', cat: '蔬菜', img: '/ingredient-images/49.jpg' },
  { name: '大葱', avg: 100, unit: '个', cat: '蔬菜', img: '/ingredient-images/50.jpg' },
  { name: '姜', avg: 30, unit: '个', cat: '调味', img: '/ingredient-images/51.jpg' },
  { name: '蒜', avg: 40, unit: '个', cat: '调味', img: '/ingredient-images/52.jpg' },
  { name: '香菜', avg: 30, unit: '个', cat: '蔬菜', img: '/ingredient-images/53.jpg' },
  { name: '鸡蛋', avg: 50, unit: '个', cat: '肉蛋', img: '/ingredient-images/54.jpg' },
  { name: '鸭蛋', avg: 60, unit: '个', cat: '肉蛋', img: '/ingredient-images/55.jpg' },
  { name: '鹌鹑蛋', avg: 10, unit: '个', cat: '肉蛋', img: '/ingredient-images/56.jpg' },
  { name: '鸡胸肉', avg: 300, unit: '个', cat: '肉蛋', img: '/ingredient-images/57.jpg' },
  { name: '鸡腿', avg: 200, unit: '个', cat: '肉蛋', img: '/ingredient-images/58.jpg' },
  { name: '鸡翅', avg: 60, unit: '个', cat: '肉蛋', img: '/ingredient-images/59.jpg' },
  { name: '鸡爪', avg: 30, unit: '个', cat: '肉蛋', img: '/ingredient-images/60.jpg' },
  { name: '猪肉', avg: 500, unit: '斤', cat: '肉类', img: '/ingredient-images/61.jpg' },
  { name: '五花肉', avg: 500, unit: '个', cat: '肉类', img: '/ingredient-images/62.jpg' },
  { name: '里脊', avg: 400, unit: '条', cat: '肉类', img: '/ingredient-images/63.jpg' },
  { name: '排骨', avg: 500, unit: '斤', cat: '肉类', img: '/ingredient-images/64.jpg' },
  { name: '牛肉', avg: 500, unit: '斤', cat: '肉类', img: '/ingredient-images/65.jpg' },
  { name: '牛腩', avg: 500, unit: '斤', cat: '肉类', img: '/ingredient-images/66.jpg' },
  { name: '羊肉', avg: 500, unit: '斤', cat: '肉类', img: '/ingredient-images/67.jpg' },
  { name: '腊肉', avg: 300, unit: '个', cat: '肉类', img: '/ingredient-images/68.jpg' },
  { name: '香肠', avg: 80, unit: '个', cat: '肉类', img: '/ingredient-images/69.jpg' },
  { name: '火腿', avg: 300, unit: '个', cat: '肉类', img: '/ingredient-images/70.jpg' },
  { name: '培根', avg: 20, unit: '片', cat: '肉类', img: '/ingredient-images/71.jpg' },
  { name: '鲈鱼', avg: 600, unit: '条', cat: '水产', img: '/ingredient-images/72.jpg' },
  { name: '草鱼', avg: 1500, unit: '条', cat: '水产', img: '/ingredient-images/73.jpg' },
  { name: '鲫鱼', avg: 300, unit: '条', cat: '水产', img: '/ingredient-images/74.jpg' },
  { name: '桂鱼', avg: 750, unit: '条', cat: '水产', img: '/ingredient-images/75.jpg' },
  { name: '带鱼', avg: 400, unit: '条', cat: '水产', img: '/ingredient-images/76.jpg' },
  { name: '多宝鱼', avg: 700, unit: '条', cat: '水产', img: '/ingredient-images/77.jpg' },
  { name: '三文鱼', avg: 300, unit: '个', cat: '水产', img: '/ingredient-images/78.jpg' },
  { name: '虾', avg: 15, unit: '个', cat: '水产', img: '/ingredient-images/79.jpg' },
  { name: '虾仁', avg: null, unit: 'g', cat: '水产', img: '/ingredient-images/80.jpg' },
  { name: '螃蟹', avg: 150, unit: '个', cat: '水产', img: '/ingredient-images/81.jpg' },
  { name: '蛤蜊', avg: 500, unit: '斤', cat: '水产', img: '/ingredient-images/82.jpg' },
  { name: '鱿鱼', avg: 300, unit: '条', cat: '水产', img: '/ingredient-images/83.jpg' },
  { name: '大米', avg: null, unit: 'g', cat: '主食', img: '/ingredient-images/84.jpg' },
  { name: '面粉', avg: null, unit: 'g', cat: '主食', img: '/ingredient-images/85.jpg' },
  { name: '面条', avg: 200, unit: '个', cat: '主食', img: '/ingredient-images/86.jpg' },
  { name: '挂面', avg: 200, unit: '个', cat: '主食', img: '/ingredient-images/87.jpg' },
  { name: '馒头', avg: 100, unit: '个', cat: '主食', img: '/ingredient-images/88.jpg' },
  { name: '米饭', avg: 200, unit: '个', cat: '主食', img: '/ingredient-images/89.jpg' },
  { name: '面包', avg: 30, unit: '片', cat: '主食', img: '/ingredient-images/90.jpg' },
  { name: '饺子皮', avg: null, unit: 'g', cat: '主食', img: '/ingredient-images/91.jpg' },
  { name: '苹果', avg: 200, unit: '个', cat: '水果', img: '/ingredient-images/92.jpg' },
  { name: '香蕉', avg: 120, unit: '个', cat: '水果', img: '/ingredient-images/93.jpg' },
  { name: '橙子', avg: 200, unit: '个', cat: '水果', img: '/ingredient-images/94.jpg' },
  { name: '柠檬', avg: 100, unit: '个', cat: '水果', img: '/ingredient-images/95.jpg' },
  { name: '梨', avg: 250, unit: '个', cat: '水果', img: '/ingredient-images/96.jpg' },
  { name: '葡萄', avg: 500, unit: '个', cat: '水果', img: '/ingredient-images/97.jpg' },
  { name: '草莓', avg: null, unit: 'g', cat: '水果', img: '/ingredient-images/98.jpg' },
  { name: '蓝莓', avg: null, unit: 'g', cat: '水果', img: '/ingredient-images/99.jpg' },
  { name: '西瓜', avg: 4000, unit: '个', cat: '水果', img: '/ingredient-images/100.jpg' },
  { name: '哈密瓜', avg: 1500, unit: '个', cat: '水果', img: '/ingredient-images/101.jpg' },
  { name: '桃', avg: 200, unit: '个', cat: '水果', img: '/ingredient-images/102.jpg' },
  { name: '猕猴桃', avg: 100, unit: '个', cat: '水果', img: '/ingredient-images/103.jpg' },
  { name: '芒果', avg: 250, unit: '个', cat: '水果', img: '/ingredient-images/104.jpg' },
  { name: '牛油果', avg: 150, unit: '个', cat: '水果', img: '/ingredient-images/105.jpg' },
  { name: '菠萝', avg: 1000, unit: '个', cat: '水果', img: '/ingredient-images/106.jpg' },
  { name: '生抽', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/107.jpg' },
  { name: '老抽', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/108.jpg' },
  { name: '香醋', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/109.jpg' },
  { name: '料酒', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/110.jpg' },
  { name: '蚝油', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/111.jpg' },
  { name: '香油', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/112.jpg' },
  { name: '食用油', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/113.jpg' },
  { name: '食盐', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/114.jpg' },
  { name: '白糖', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/115.jpg' },
  { name: '淀粉', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/116.jpg' },
  { name: '胡椒粉', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/117.jpg' },
  { name: '花椒', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/118.jpg' },
  { name: '八角', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/119.jpg' },
  { name: '干辣椒', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/120.jpg' },
  { name: '豆瓣酱', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/121.jpg' },
  { name: '甜面酱', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/122.jpg' },
  { name: '番茄酱', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/123.jpg' },
  { name: '蜂蜜', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/124.jpg' },
  { name: '芝麻酱', avg: null, unit: '毫升', cat: '调味', img: '/ingredient-images/125.jpg' },
  { name: '白芝麻', avg: null, unit: 'g', cat: '调味', img: '/ingredient-images/126.jpg' },
  { name: '牛奶', avg: null, unit: '毫升', cat: '乳制品', img: '/ingredient-images/127.jpg' },
  { name: '酸奶', avg: null, unit: '毫升', cat: '乳制品', img: '/ingredient-images/128.jpg' },
  { name: '黄油', avg: 200, unit: '个', cat: '乳制品', img: '/ingredient-images/129.jpg' },
  { name: '淡奶油', avg: null, unit: '毫升', cat: '乳制品', img: '/ingredient-images/130.jpg' },
  { name: '芝士', avg: 20, unit: '片', cat: '乳制品', img: '/ingredient-images/131.jpg' },
  { name: '红枣', avg: null, unit: 'g', cat: '干货', img: '/ingredient-images/132.jpg' },
  { name: '枸杞', avg: null, unit: 'g', cat: '干货', img: '/ingredient-images/133.jpg' },
  { name: '花生米', avg: null, unit: 'g', cat: '干货', img: '/ingredient-images/134.jpg' },
  { name: '核桃', avg: 10, unit: '个', cat: '干货', img: '/ingredient-images/135.jpg' },
  { name: '豆浆', avg: 250, unit: '个', cat: '饮品', img: '/ingredient-images/136.jpg' },
]

/** 可选单位：只用能精确计量的（个/条/片 按平均大小折算克数） */
export const UNIT_OPTIONS = ['个', 'g', 'kg', '斤', '毫升', '条', '片']

/** 可按「平均单个重量」折算克数的计数单位 */
export const COUNT_UNITS = ['个', '条', '片']

/** 不同单位的输入步长（g/毫升 每次 10，其余 0.5） */
export const UNIT_STEP = { g: 10, 毫升: 10, kg: 0.5, 斤: 0.5, 个: 0.5, 条: 1, 片: 1 }

const CAT_EMOJI = {
  蔬菜: '🥬', 菌菇: '🍄', 豆制品: '🧊', 肉蛋: '🥚', 肉类: '🍖', 水产: '🐟',
  主食: '🍚', 水果: '🍎', 调味: '🧂', 乳制品: '🥛', 干货: '🌰', 饮品: '🥤',
}

/** 名称最长匹配（'小番茄' 能匹配到 '番茄'）；找不到返回兜底对象 */
export function matchIngredient(name) {
  const n = String(name || '').trim()
  if (!n) return {}
  let best = null
  for (const it of INGREDIENTS) {
    if (n.includes(it.name) && (!best || it.name.length > best.name.length)) best = it
  }
  if (best) return { ...best, emoji: CAT_EMOJI[best.cat] || '🥗' }
  return { name: n, emoji: '🥗', avg: null, unit: 'g', cat: '未收录', img: null }
}

/**
 * 把「数量 + 单位」折算成克。
 * - g / kg / 斤 / 毫升 直接换算（毫升按密度≈1 处理）
 * - 个 / 条 / 片 按食材平均单个重量折算（如 1 个苹果≈200g）
 * - 无法确定时返回 null（页面不显示估算，避免误导）
 */
export function toGrams(name, qty, unit) {
  const q = Number(qty)
  if (!q || q <= 0 || !unit) return null
  if (unit === 'g') return q
  if (unit === 'kg') return q * 1000
  if (unit === '斤') return q * 500
  if (unit === '毫升') return q
  if (COUNT_UNITS.includes(unit)) {
    const m = matchIngredient(name)
    return m.avg ? q * m.avg : null
  }
  return null
}

/** 克数格式化：<1000g 显示 g，否则显示 kg */
export function fmtWeight(g) {
  if (!g && g !== 0) return ''
  if (g < 1000) return `${Math.round(g)}g`
  return `${(g / 1000).toFixed(1)}kg`
}
