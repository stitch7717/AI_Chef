<template>
  <el-container class="layout">
    <!-- 侧边栏：桌面端固定 -->
    <el-aside width="228px" class="aside-desktop">
      <div class="logo-area">
        <div class="logo-mark">🍳</div>
        <div class="logo-text">
          <div class="logo-name">AI 私厨</div>
          <div class="logo-slogan">你的私人厨师</div>
        </div>
      </div>

      <el-menu :default-active="active" router class="side-menu">
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon><span>AI 对话</span>
        </el-menu-item>
        <el-menu-item index="/pantry">
          <el-icon><Goods /></el-icon><span>我的库存</span>
        </el-menu-item>
        <el-menu-item index="/recipes">
          <el-icon><Compass /></el-icon><span>发现菜谱</span>
        </el-menu-item>
      </el-menu>

      <div class="user-card">
        <div class="avatar">{{ initial }}</div>
        <div class="user-meta">
          <div class="nickname">{{ auth.user?.nickname || '用户' }}</div>
          <div class="user-sub">已登录</div>
        </div>
        <el-tooltip content="退出登录" placement="top">
          <el-icon class="logout" @click="logout"><SwitchButton /></el-icon>
        </el-tooltip>
      </div>
    </el-aside>

    <el-main class="main">
      <router-view />

      <!-- 移动端底部 Tab 栏 -->
      <nav class="tabbar">
        <router-link to="/chat" class="tab" :class="{ on: active === '/chat' }">
          <el-icon><ChatDotRound /></el-icon><span>对话</span>
        </router-link>
        <router-link to="/pantry" class="tab" :class="{ on: active === '/pantry' }">
          <el-icon><Goods /></el-icon><span>库存</span>
        </router-link>
        <router-link to="/recipes" class="tab" :class="{ on: active === '/recipes' }">
          <el-icon><Compass /></el-icon><span>发现</span>
        </router-link>
      </nav>
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, Goods, Compass, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const active = computed(() => route.path)
const initial = computed(() => (auth.user?.nickname || '用')[0].toUpperCase())

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100%; }

.aside-desktop {
  display: flex; flex-direction: column;
  background: var(--card);
  border-right: 1px solid var(--ink-100);
}

.logo-area {
  display: flex; align-items: center; gap: 10px;
  padding: 22px 20px 18px;
}
.logo-mark {
  width: 40px; height: 40px; border-radius: 12px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-600));
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(61, 127, 255, .28);
}
.logo-name { font-size: 17px; font-weight: 800; color: var(--ink-900); letter-spacing: .5px; }
.logo-slogan { font-size: 11px; color: var(--ink-400); margin-top: 1px; }

.side-menu { border-right: none; flex: 1; padding: 0 12px; background: transparent; }
.side-menu .el-menu-item {
  height: 44px; margin-bottom: 6px; border-radius: 12px;
  color: var(--ink-600); font-size: 14px;
  transition: all .18s ease;
}
.side-menu .el-menu-item:hover { background: var(--ink-100); color: var(--ink-900); }
.side-menu .el-menu-item.is-active {
  background: var(--brand-50); color: var(--brand-600); font-weight: 700;
}
.side-menu .el-menu-item.is-active .el-icon { color: var(--brand-600); }

.user-card {
  margin: 12px; padding: 12px;
  display: flex; align-items: center; gap: 10px;
  background: var(--ink-100); border-radius: 14px;
}
.avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-600));
  color: #fff; font-weight: 700; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.user-meta { flex: 1; min-width: 0; }
.nickname { font-size: 13px; font-weight: 600; color: var(--ink-900); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-sub { font-size: 11px; color: var(--ink-400); }
.logout { color: var(--ink-400); cursor: pointer; transition: color .15s; }
.logout:hover { color: var(--danger); }

.main { padding: 0; background: var(--surface); }

/* ---- 移动端底部 Tab ---- */
.tabbar { display: none; }

@media (max-width: 768px) {
  .aside-desktop { display: none; }
  .main { padding: 0 0 58px; }
  .tabbar {
    display: flex; position: fixed; left: 0; right: 0; bottom: 0; z-index: 100;
    height: 56px; background: rgba(255, 255, 255, .96); backdrop-filter: blur(12px);
    border-top: 1px solid var(--ink-100);
  }
  .tab {
    flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 2px; font-size: 10px; color: var(--ink-400); text-decoration: none;
  }
  .tab .el-icon { font-size: 20px; }
  .tab.on { color: var(--brand-600); font-weight: 700; }
}
</style>
