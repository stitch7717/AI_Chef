<template>
  <div class="chat-page">
    <!-- 会话侧栏 -->
    <div class="session-bar">
      <el-button type="primary" class="new-btn" @click="newSession">
        <el-icon style="margin-right:4px"><Plus /></el-icon> 新对话
      </el-button>
      <div class="session-list">
        <div v-for="s in sessions" :key="s.id"
             class="session-item" :class="{ active: s.id === currentId }"
             @click="switchSession(s.id)">
          <span class="dot"></span>
          <span class="title">{{ s.title }}</span>
          <el-icon class="del" @click.stop="removeSession(s.id)"><Delete /></el-icon>
        </div>
      </div>
    </div>

    <!-- 消息区 -->
    <div class="chat-main">
      <!-- 移动端顶栏：打开会话抽屉 -->
      <div class="mobile-bar">
        <button class="mb-btn" @click="drawer = true">☰</button>
        <span class="mb-title">{{ currentTitle }}</span>
        <button class="mb-btn" @click="newSession">＋</button>
      </div>

      <div ref="msgBox" class="msg-box">
        <template v-if="messages.length === 0 && !streaming">
          <div class="empty">
            <div class="empty-icon">👨‍🍳</div>
            <h3>今天想吃点什么？</h3>
            <p>告诉我你有什么食材，或者拍张冰箱照片</p>
            <div class="chips">
              <span v-for="q in suggestions" :key="q" class="chip" @click="input = q">
                {{ q }}
              </span>
            </div>
          </div>
        </template>
        <div v-for="m in messages" :key="m.id" class="msg" :class="m.role">
          <div class="avatar">{{ m.role === 'user' ? '🧑' : '👨‍🍳' }}</div>
          <div class="bubble">
            <img v-if="m.image_url" :src="m.image_url" class="msg-img" />
            <div class="text">{{ m.content }}</div>
          </div>
        </div>
        <!-- 流式中的消息 -->
        <div v-if="streaming" class="msg assistant">
          <div class="avatar">👨‍🍳</div>
          <div class="bubble">
            <img v-if="pendingImage" :src="pendingImage" class="msg-img" />
            <div class="text">{{ streamText }}<span class="cursor">▌</span></div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-wrap">
        <div v-if="pendingImage" class="img-preview">
          <img :src="pendingImage" />
          <el-icon class="remove" @click="pendingImage = ''"><Close /></el-icon>
        </div>
        <div class="input-bar">
          <el-upload :show-file-list="false" accept="image/*" :before-upload="handleUpload">
            <el-button circle class="upload-btn" :loading="uploading">
              <el-icon><Picture /></el-icon>
            </el-button>
          </el-upload>
          <el-input v-model="input" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }"
                    placeholder="问我做什么菜…（Enter 发送）" @keydown.enter.exact.prevent="send" />
          <el-button type="primary" class="send-btn" :loading="streaming" @click="send">
            <el-icon v-if="!streaming"><Promotion /></el-icon>
          </el-button>
        </div>
        <div class="input-hint">AI 可能会出错，请注意食材安全与过敏原</div>
      </div>
    </div>

    <!-- 移动端会话抽屉 -->
    <el-drawer v-model="drawer" direction="ltr" size="78%" :with-header="false" class="session-drawer">
      <div class="drawer-inner">
        <el-button type="primary" class="new-btn" @click="newSessionFromDrawer">
          <el-icon style="margin-right:4px"><Plus /></el-icon> 新对话
        </el-button>
        <div class="drawer-list">
          <div v-for="s in sessions" :key="s.id" class="session-item"
               :class="{ active: s.id === currentId }"
               @click="switchFromDrawer(s.id)">
            <span class="dot"></span>
            <span class="title">{{ s.title }}</span>
            <el-icon class="del" @click.stop="removeSession(s.id)"><Delete /></el-icon>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Close, Picture, Plus, Promotion } from '@element-plus/icons-vue'
import { api, streamChat, uploadImage, errMsg } from '../api'

const sessions = ref([])
const currentId = ref(null)
const messages = ref([])
const input = ref('')
const streaming = ref(false)
const streamText = ref('')
const pendingImage = ref('')
const uploading = ref(false)
const msgBox = ref(null)
const drawer = ref(false)

const currentTitle = computed(() => {
  const s = sessions.value.find((x) => x.id === currentId.value)
  return s?.title || 'AI 私厨'
})

const suggestions = [
  '冰箱里有鸡蛋和西红柿，能做什么菜？',
  '推荐一道 15 分钟搞定的晚餐',
  '减脂期晚上吃什么好？',
  '用土豆、洋葱和牛肉做一道硬菜',
]

function scrollBottom() {
  nextTick(() => { if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight })
}

onMounted(async () => {
  const { data } = await api.listSessions({ limit: 50 })
  sessions.value = data
  if (data.length) await switchSession(data[0].id)
  else await newSession()
})

async function refreshSessions() {
  const { data } = await api.listSessions({ limit: 50 })
  sessions.value = data
}

async function newSessionFromDrawer() {
  await newSession()
  drawer.value = false
}

async function switchFromDrawer(id) {
  await switchSession(id)
  drawer.value = false
}

async function newSession() {
  const { data } = await api.createSession({ title: '新对话' })
  sessions.value.unshift(data)
  currentId.value = data.id
  messages.value = []
}

async function switchSession(id) {
  currentId.value = id
  const { data } = await api.listMessages(id)
  messages.value = data
  scrollBottom()
}

async function removeSession(id) {
  await ElMessageBox.confirm('删除这个对话？历史消息将一并删除', '提示', { type: 'warning' })
  await api.deleteSession(id)
  sessions.value = sessions.value.filter((s) => s.id !== id)
  if (currentId.value === id) {
    if (sessions.value.length) await switchSession(sessions.value[0].id)
    else await newSession()
  }
}

async function handleUpload(file) {
  uploading.value = true
  try {
    pendingImage.value = await uploadImage(file)
    ElMessage.success('图片已上传')
  } catch (e) { ElMessage.error(errMsg(e)) } finally { uploading.value = false }
  return false   // 阻止 el-upload 默认行为
}

async function send() {
  const text = input.value.trim()
  if (!text && !pendingImage.value) return
  if (streaming.value) return

  // 本地先显示用户消息
  messages.value.push({ id: Date.now(), role: 'user', content: text || '（发了一张图）', image_url: pendingImage.value || null })
  const img = pendingImage.value
  input.value = ''
  pendingImage.value = ''
  streaming.value = true
  streamText.value = ''
  scrollBottom()

  await streamChat(currentId.value, { message: text || '帮我看看这张图里有什么食材', image_url: img || null }, {
    onToken(t) { streamText.value += t; scrollBottom() },
    onDone() {
      streaming.value = false
      messages.value.push({ id: Date.now() + 1, role: 'assistant', content: streamText.value, image_url: null })
      streamText.value = ''
      refreshSessions()   // 标题可能已更新
      scrollBottom()
    },
    onError(detail) {
      streaming.value = false
      ElMessage.error(detail)
      if (streamText.value) {
        messages.value.push({ id: Date.now() + 1, role: 'assistant', content: streamText.value, image_url: null })
      }
      streamText.value = ''
    },
  })
}
</script>

<style scoped>
.chat-page { display: flex; height: 100%; }

/* ---- 会话侧栏 ---- */
.session-bar {
  width: 240px; border-right: 1px solid var(--ink-100);
  padding: 16px 12px; display: flex; flex-direction: column; gap: 12px;
  background: var(--card);
}
.new-btn { width: 100%; border-radius: 12px; font-weight: 700; }
.session-list { overflow-y: auto; flex: 1; }
.session-item {
  padding: 10px 12px; border-radius: 12px; cursor: pointer;
  display: flex; align-items: center; gap: 8px; font-size: 13px;
  color: var(--ink-600); transition: all .15s ease; margin-bottom: 2px;
}
.session-item:hover { background: var(--ink-100); }
.session-item.active { background: var(--brand-50); color: var(--brand-700); font-weight: 600; }
.session-item .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--ink-200); flex-shrink: 0;
}
.session-item.active .dot { background: var(--brand-500); }
.session-item .title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-item .del { opacity: 0; color: var(--danger); transition: opacity .15s; }
.session-item:hover .del { opacity: 1; }

/* ---- 消息区 ---- */
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.msg-box { flex: 1; overflow-y: auto; padding: 24px 32px; }

.empty { text-align: center; margin-top: 18vh; color: var(--ink-400); }
.empty-icon {
  width: 88px; height: 88px; margin: 0 auto 18px; border-radius: 50%;
  background: var(--brand-50); display: flex; align-items: center; justify-content: center;
  font-size: 44px;
}
.empty h3 { font-size: 20px; color: var(--ink-900); margin-bottom: 6px; }
.empty p { font-size: 14px; }
.chips { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 22px; max-width: 560px; margin-left: auto; margin-right: auto; }
.chip {
  padding: 9px 16px; border-radius: 999px; font-size: 13px;
  background: var(--card); border: 1px solid var(--ink-200); color: var(--ink-600);
  cursor: pointer; transition: all .15s ease;
}
.chip:hover { border-color: var(--brand-500); color: var(--brand-600); background: var(--brand-50); }

.msg { display: flex; margin-bottom: 18px; gap: 10px; align-items: flex-start; }
.msg.user { flex-direction: row-reverse; }
.avatar {
  width: 36px; height: 36px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 19px;
  background: var(--ink-100);
}
.msg.user .avatar { background: var(--brand-50); }
.bubble {
  max-width: 72%; padding: 12px 16px; border-radius: 16px;
  font-size: 14px; line-height: 1.75;
}
.msg.user .bubble {
  background: linear-gradient(135deg, var(--brand-500), var(--brand-600));
  color: #fff; border-top-right-radius: 4px;
  box-shadow: 0 4px 14px rgba(61, 127, 255, .25);
}
.msg.assistant .bubble {
  background: var(--card); border: 1px solid var(--ink-100); color: var(--ink-900);
  border-top-left-radius: 4px; white-space: pre-wrap;
  box-shadow: 0 2px 10px rgba(28, 25, 23, .04);
}
.msg-img { max-width: 220px; border-radius: 10px; margin-bottom: 8px; display: block; }
.cursor { animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0; } }

/* ---- 输入区 ---- */
.input-wrap { padding: 0 32px 18px; }
.input-bar {
  display: flex; gap: 10px; align-items: flex-end;
  background: var(--card); border: 1px solid var(--ink-200); border-radius: 18px;
  padding: 10px 12px;
  box-shadow: 0 8px 24px rgba(28, 25, 23, .07);
  transition: border-color .15s;
}
.input-bar:focus-within { border-color: var(--brand-500); }
.input-bar :deep(.el-textarea__inner) {
  box-shadow: none; background: transparent; font-size: 14px; padding: 6px 4px;
}
.upload-btn { border: none; background: var(--ink-100); color: var(--ink-600); }
.upload-btn:hover { background: var(--brand-100); color: var(--brand-600); }
.send-btn { border-radius: 12px; width: 42px; height: 36px; }
.img-preview { position: relative; display: inline-block; margin-bottom: 8px; margin-left: 8px; }
.img-preview img { height: 64px; border-radius: 10px; }
.img-preview .remove {
  position: absolute; top: -7px; right: -7px;
  background: var(--danger); color: #fff; border-radius: 50%; padding: 2px; cursor: pointer;
}
.input-hint { text-align: center; font-size: 11px; color: var(--ink-400); margin-top: 8px; }

/* 移动端顶栏（桌面隐藏） */
.mobile-bar { display: none; }

@media (max-width: 768px) {
  .session-bar { display: none; }
  .mobile-bar {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 12px; border-bottom: 1px solid var(--ink-100);
    background: var(--card);
  }
  .mb-btn {
    width: 34px; height: 34px; border-radius: 10px; border: 1px solid var(--ink-200);
    background: var(--card); font-size: 15px; color: var(--ink-900); cursor: pointer;
  }
  .mb-title {
    flex: 1; text-align: center; font-size: 14px; font-weight: 600;
    color: var(--ink-900); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .msg-box { padding: 16px; }
  .input-wrap { padding: 0 12px 12px; }
  .bubble { max-width: 84%; }
}

/* 抽屉内容 */
.drawer-inner { display: flex; flex-direction: column; gap: 12px; height: 100%; padding: 4px; }
.drawer-list { flex: 1; overflow-y: auto; }
.drawer-inner .session-item { padding: 12px; }
</style>
