import http, { errMsg } from './http'

export { errMsg }

/** 业务接口集中封装（对标 Java 的 FeignClient） */
export const api = {
  // ---- 认证 ----
  register: (data) => http.post('/api/v1/auth/register', data),
  login: (data) => http.post('/api/v1/auth/login', data),
  me: () => http.get('/api/v1/auth/me'),

  // ---- 会话 ----
  listSessions: (params) => http.get('/api/v1/sessions', { params }),
  createSession: (data) => http.post('/api/v1/sessions', data),
  deleteSession: (id) => http.delete(`/api/v1/sessions/${id}`),
  listMessages: (id) => http.get(`/api/v1/sessions/${id}/messages`),

  // ---- 对话 ----
  invoke: (id, data) => http.post(`/api/v1/chat/${id}/invoke`, data, { timeout: 120000 }),

  // ---- 库存 ----
  listPantry: (params) => http.get('/api/v1/pantry', { params }),
  addPantry: (data) => http.post('/api/v1/pantry', data),
  updatePantry: (id, data) => http.patch(`/api/v1/pantry/${id}`, data),
  deletePantry: (id) => http.delete(`/api/v1/pantry/${id}`),

  // ---- 菜谱 / 收藏 / 反馈 ----
  listRecipes: (params) => http.get('/api/v1/recipes', { params }),
  searchRecipes: (keyword) => http.get('/api/v1/recipes/search', { params: { keyword } }),
  listFavorites: () => http.get('/api/v1/favorites'),
  addFavorite: (rid) => http.post(`/api/v1/favorites/${rid}`),
  removeFavorite: (rid) => http.delete(`/api/v1/favorites/${rid}`),
  addFeedback: (data) => http.post('/api/v1/feedbacks', data),

  // ---- 图片直传 ----
  presign: (filename) => http.get('/api/v1/oss/presign', { params: { filename } }),
}

/**
 * SSE 流式对话（fetch 实现，因为 EventSource 不支持 POST 与自定义 Header）
 * @param {number} sessionId
 * @param {{message: string, image_url?: string}} payload
 * @param {{onStart?, onToken?, onDone?, onError?}} handlers
 */
export async function streamChat(sessionId, payload, handlers) {
  const token = localStorage.getItem('token')
  const resp = await fetch(`/api/v1/chat/${sessionId}/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  })
  if (!resp.ok || !resp.body) {
    let detail = `HTTP ${resp.status}`
    try { detail = (await resp.json()).detail || detail } catch {}
    handlers.onError?.(detail)
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    // SSE 消息以空行分隔
    const blocks = buf.split('\n\n')
    buf = blocks.pop()
    for (const block of blocks) {
      let event = 'message'
      let data = ''
      for (const line of block.split('\n')) {
        if (line.startsWith('event: ')) event = line.slice(7)
        else if (line.startsWith('data: ')) data += line.slice(6)
      }
      if (!data) continue
      const parsed = JSON.parse(data)
      if (event === 'start') handlers.onStart?.(parsed)
      else if (event === 'token') handlers.onToken?.(parsed.text)
      else if (event === 'done') handlers.onDone?.(parsed)
      else if (event === 'error') handlers.onError?.(parsed.detail)
    }
  }
}

/**
 * 图片直传 OSS：①要通行证 ②PUT 上传 ③返回公开 URL
 * @param {File} file
 * @returns {Promise<string>} accessUrl
 */
export async function uploadImage(file) {
  const { data } = await api.presign(file.name)
  await fetch(data.uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': data.contentType },
    body: file,
  })
  return data.accessUrl
}
