import axios from 'axios'

/**
 * 全局 axios 实例（对标 Java 的 RestTemplate/Feign 拦截器）：
 * - 请求拦截：自动带上 Bearer token
 * - 响应拦截：401 时清掉本地登录态并跳登录页
 */
const http = axios.create({
  baseURL: '',           // 开发环境走 vite 代理（同源），生产由 Nginx 反代
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!location.pathname.startsWith('/login')) {
        location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

/** 从后端错误响应里提取可读信息 */
export function errMsg(e) {
  return e.response?.data?.detail || e.message || '请求失败'
}

export default http
