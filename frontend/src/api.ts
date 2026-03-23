const API = '/api'

function getToken(): string | null {
  return localStorage.getItem('token')
}

export async function authFetch(
  path: string,
  options: RequestInit & { skipAuth?: boolean } = {}
): Promise<Response> {
  const { skipAuth, ...init } = options
  const headers = new Headers(init.headers)
  if (!skipAuth) {
    const token = getToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }
  const isFormData = init.body instanceof FormData
  const isBlob = init.body instanceof Blob
  if (!isFormData && !isBlob && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  return fetch(`${API}${path}`, { ...init, headers })
}

export async function signup(email: string, password: string) {
  const res = await authFetch('/auth/signup', {
    method: 'POST',
    skipAuth: true,
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(d.detail ?? '注册失败')
  }
  return res.json()
}

export async function login(email: string, password: string) {
  const res = await authFetch('/auth/login', {
    method: 'POST',
    skipAuth: true,
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(d.detail ?? '登录失败')
  }
  return res.json()
}

export async function me() {
  const res = await authFetch('/auth/me')
  if (!res.ok) throw new Error('未登录')
  return res.json()
}

function formatApiError(d: { detail?: unknown }): string {
  const { detail } = d
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((x: { msg?: string }) => x.msg ?? JSON.stringify(x)).join('; ')
  }
  return '请求失败'
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const res = await authFetch('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  })
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(formatApiError(d))
  }
}

export async function listFiles(): Promise<{ id: number; filename: string; status: string }[]> {
  const res = await authFetch('/files')
  if (!res.ok) throw new Error('获取文件列表失败')
  return res.json()
}

export async function uploadFile(file: File): Promise<{ file_id: number; filename: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await authFetch('/files/upload', { method: 'POST', body: form })
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(d.detail ?? '上传失败')
  }
  return res.json()
}

export async function processFile(fileId: number): Promise<{ file_id: number; status: string; pages?: number; chunks?: number }> {
  const res = await authFetch(`/files/${fileId}/process`, { method: 'POST' })
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(d.detail ?? '处理失败')
  }
  return res.json()
}

export async function chat(fileId: number, query: string): Promise<{ answer: string; citations: { page: number; snippet: string }[] }> {
  const res = await authFetch('/chat', {
    method: 'POST',
    body: JSON.stringify({ file_id: fileId, query }),
  })
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(d.detail ?? '对话失败')
  }
  return res.json()
}
