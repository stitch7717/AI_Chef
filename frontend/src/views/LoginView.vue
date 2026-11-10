<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-panel">
      <div class="deco deco-1">🍅</div>
      <div class="deco deco-2">🥦</div>
      <div class="deco deco-3">🥕</div>
      <!-- Orea 风白色圆形数据徽章 -->
      <div class="float-badge badge-1"><span class="fb-icon fb-red">🔥</span><div><b>341 kcal</b><small>卡路里</small></div></div>
      <div class="float-badge badge-2"><span class="fb-icon fb-green">🥑</span><div><b>37.6 g</b><small>脂肪</small></div></div>
      <div class="float-badge badge-3"><span class="fb-icon fb-amber">🍗</span><div><b>43.5 g</b><small>蛋白质</small></div></div>
      <div class="brand-inner">
        <div class="brand-logo">🍳</div>
        <h1 class="brand-name">AI 私厨</h1>
        <p class="brand-slogan">会看图、懂菜谱、记得你的私人厨师</p>
        <div class="features">
          <div class="feature">
            <span class="f-icon">📸</span>
            <div><b>拍一拍就知道</b><small>拍张冰箱照片，自动识别现有食材</small></div>
          </div>
          <div class="feature">
            <span class="f-icon">🧠</span>
            <div><b>越用越懂你</b><small>记住你的口味与历史推荐</small></div>
          </div>
          <div class="feature">
            <span class="f-icon">🥘</span>
            <div><b>有什么做什么</b><small>按库存智能推荐，不浪费食材</small></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="form-panel">
      <div class="form-box">
        <div class="form-head">
          <div class="m-logo">🍳</div>
          <h2>{{ tab === 'login' ? '欢迎回来' : '创建账号' }}</h2>
          <p>{{ tab === 'login' ? '登录后继续你的美食之旅' : '一分钟注册，开始做菜' }}</p>
        </div>

        <el-tabs v-model="tab" stretch class="auth-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form @submit.prevent="doLogin">
              <el-form-item>
                <el-input v-model="loginForm.username" placeholder="用户名" size="large">
                  <template #prefix><el-icon><User /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-input v-model="loginForm.password" type="password" show-password
                          placeholder="密码" size="large" @keyup.enter="doLogin">
                  <template #prefix><el-icon><Lock /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-button type="primary" size="large" class="w100 submit-btn" :loading="loading"
                         @click="doLogin">登 录</el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form @submit.prevent="doRegister">
              <el-form-item>
                <el-input v-model="regForm.username" placeholder="用户名（3-50字符）" size="large">
                  <template #prefix><el-icon><User /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-input v-model="regForm.password" type="password" show-password
                          placeholder="密码（至少6位）" size="large">
                  <template #prefix><el-icon><Lock /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-input v-model="regForm.nickname" placeholder="昵称（可选）" size="large">
                  <template #prefix><el-icon><Postcard /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-button type="primary" size="large" class="w100 submit-btn" :loading="loading"
                         @click="doRegister">注 册 并 登 录</el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <p v-if="error" class="error">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Postcard } from '@element-plus/icons-vue'
import { api, errMsg } from '../api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const tab = ref('login')
const loading = ref(false)
const error = ref('')

const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', password: '', nickname: '' })

async function doLogin() {
  if (!loginForm.username || !loginForm.password) { error.value = '请输入用户名和密码'; return }
  loading.value = true; error.value = ''
  try {
    const { data } = await api.login(loginForm)
    await auth.setAuth(data.access_token, null)
    await auth.fetchMe()
    ElMessage.success('欢迎回来！')
    router.push('/chat')
  } catch (e) { error.value = errMsg(e) } finally { loading.value = false }
}

async function doRegister() {
  if (!regForm.username || !regForm.password) { error.value = '请输入用户名和密码'; return }
  loading.value = true; error.value = ''
  try {
    await api.register(regForm)
    const { data } = await api.login({ username: regForm.username, password: regForm.password })
    await auth.setAuth(data.access_token, null)
    await auth.fetchMe()
    ElMessage.success('注册成功，开始做菜吧！')
    router.push('/chat')
  } catch (e) { error.value = errMsg(e) } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { height: 100%; display: flex; }

/* ---- 左侧品牌区 ---- */
.brand-panel {
  flex: 1.1; position: relative; overflow: hidden;
  background: linear-gradient(155deg, #eef4fb 0%, #dce9f7 48%, #c9ddf5 100%);
  display: flex; align-items: center; justify-content: center;
}
.brand-inner { max-width: 420px; padding: 40px; position: relative; z-index: 2; }
.brand-logo {
  width: 72px; height: 72px; border-radius: 22px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-600));
  display: flex; align-items: center; justify-content: center;
  font-size: 36px; margin-bottom: 22px;
  box-shadow: 0 12px 30px rgba(61, 127, 255, .3);
}
.brand-name { font-size: 40px; font-weight: 800; color: var(--ink-900); letter-spacing: 2px; }
.brand-slogan { font-size: 15px; color: var(--ink-600); margin: 10px 0 36px; }

.features { display: flex; flex-direction: column; gap: 20px; }
.feature { display: flex; gap: 14px; align-items: flex-start; }
.f-icon {
  width: 44px; height: 44px; border-radius: 14px; background: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 22px;
  box-shadow: 0 4px 14px rgba(28, 25, 23, .07); flex-shrink: 0;
}
.feature b { display: block; font-size: 15px; color: var(--ink-900); }
.feature small { font-size: 13px; color: var(--ink-600); }

.deco { position: absolute; font-size: 46px; opacity: .22; filter: blur(1px); }
.deco-1 { top: 8%; right: 12%; transform: rotate(15deg); }
.deco-2 { bottom: 14%; right: 8%; transform: rotate(-12deg); font-size: 60px; }
.deco-3 { top: 52%; left: 6%; transform: rotate(8deg); font-size: 38px; }

/* Orea 风白色圆形数据徽章 */
.float-badge {
  position: absolute; z-index: 3;
  display: flex; align-items: center; gap: 8px;
  background: rgba(255, 255, 255, .92); backdrop-filter: blur(6px);
  border-radius: 999px; padding: 8px 16px 8px 9px;
  box-shadow: 0 10px 28px rgba(28, 43, 74, .12);
  animation: floaty 4s ease-in-out infinite;
}
.float-badge b { display: block; font-size: 14px; color: var(--ink-900); line-height: 1.1; }
.float-badge small { font-size: 11px; color: var(--ink-400); }
.fb-icon {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 15px;
}
.fb-red { background: #ffeceb; }
.fb-green { background: #e6f8f1; }
.fb-amber { background: #fff4e0; }
.badge-1 { top: 13%; left: 8%; }
.badge-2 { top: 24%; right: 7%; animation-delay: -1.4s; }
.badge-3 { bottom: 10%; left: 13%; animation-delay: -2.6s; }
@keyframes floaty {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-9px); }
}

/* ---- 右侧表单区 ---- */
.form-panel {
  flex: 1; display: flex; align-items: center; justify-content: center;
  background: var(--card); padding: 32px;
}
.form-box { width: 380px; max-width: 100%; }
.form-head { text-align: center; margin-bottom: 8px; }
.m-logo { display: none; }
.form-head h2 { font-size: 24px; font-weight: 800; color: var(--ink-900); }
.form-head p { font-size: 13px; color: var(--ink-400); margin: 6px 0 18px; }

.auth-tabs :deep(.el-tabs__item) { font-size: 15px; font-weight: 600; }
.auth-tabs :deep(.el-tabs__nav-wrap::after) { height: 1px; background: var(--ink-100); }

.submit-btn { margin-top: 6px; letter-spacing: 4px; border-radius: 12px; }
.w100 { width: 100%; }
.error { color: var(--danger); font-size: 13px; margin-top: 12px; text-align: center; }

/* ---- 移动端：只保留表单，顶部加品牌 ---- */
@media (max-width: 860px) {
  .brand-panel { display: none; }
  .m-logo {
    display: flex; width: 56px; height: 56px; border-radius: 18px;
    background: linear-gradient(135deg, var(--brand-500), var(--brand-600));
    align-items: center; justify-content: center; font-size: 28px;
    margin: 0 auto 14px; box-shadow: 0 8px 20px rgba(61, 127, 255, .28);
  }
}
</style>
