import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    redirect: '/chat',
    children: [
      { path: 'chat', name: 'chat', component: () => import('../views/ChatView.vue'), meta: { title: 'AI 对话' } },
      { path: 'pantry', name: 'pantry', component: () => import('../views/PantryView.vue'), meta: { title: '我的库存' } },
      { path: 'recipes', name: 'recipes', component: () => import('../views/RecipesView.vue'), meta: { title: '菜谱库' } },
    ],
  },
  // 兜底：未知路径回到首页（避免白屏）
  { path: '/:pathMatch(.*)*', redirect: '/chat' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：未登录一律踢回登录页（对标 Spring Security 的认证过滤器）
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!token && to.name !== 'login') return { name: 'login' }
  if (token && to.name === 'login') return { name: 'chat' }
})

export default router
