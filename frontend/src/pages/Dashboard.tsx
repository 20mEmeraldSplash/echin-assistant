import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import * as api from '../api'
import './Dashboard.css'

type FileItem = { id: number; filename: string; status: string }
type Message = { role: 'user' | 'assistant'; content: string; citations?: { page: number; snippet: string }[] }

export default function Dashboard() {
  const { user, logout } = useAuth()
  const [files, setFiles] = useState<FileItem[]>([])
  const [loadingFiles, setLoadingFiles] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [processingId, setProcessingId] = useState<number | null>(null)
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const loadFiles = async () => {
    setLoadingFiles(true)
    try {
      const list = await api.listFiles()
      setFiles(list)
    } catch {
      setFiles([])
    } finally {
      setLoadingFiles(false)
    }
  }

  useEffect(() => {
    loadFiles()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      alert('请选择 PDF 文件')
      return
    }
    setUploading(true)
    try {
      await api.uploadFile(file)
      await loadFiles()
    } catch (err) {
      alert(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleProcess = async (fileId: number) => {
    setProcessingId(fileId)
    try {
      await api.processFile(fileId)
      await loadFiles()
    } catch (err) {
      alert(err instanceof Error ? err.message : '处理失败')
    } finally {
      setProcessingId(null)
    }
  }

  const handleSend = async () => {
    const q = input.trim()
    if (!q || !selectedFileId) return
    setMessages((m) => [...m, { role: 'user', content: q }])
    setInput('')
    setSending(true)
    try {
      const { answer, citations } = await api.chat(selectedFileId, q)
      setMessages((m) => [...m, { role: 'assistant', content: answer, citations }])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: (err instanceof Error ? err.message : '请求失败') },
      ])
    } finally {
      setSending(false)
    }
  }

  const readyFiles = files.filter((f) => f.status === 'READY')

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1 className="dashboard-title">EChin Assistant</h1>
        <div className="dashboard-user">
          <span className="dashboard-email">{user?.email}</span>
          <button type="button" onClick={logout} className="dashboard-logout">
            退出
          </button>
        </div>
      </header>

      <div className="dashboard-body">
        <aside className="dashboard-sidebar">
          <section className="sidebar-section">
            <h2>上传 PDF</h2>
            <label className="upload-btn">
              <input
                type="file"
                accept=".pdf"
                onChange={handleUpload}
                disabled={uploading}
                hidden
              />
              {uploading ? '上传中…' : '选择 PDF 上传'}
            </label>
          </section>

          <section className="sidebar-section">
            <h2>我的文件</h2>
            {loadingFiles ? (
              <p className="sidebar-muted">加载中…</p>
            ) : files.length === 0 ? (
              <p className="sidebar-muted">暂无文件，请先上传</p>
            ) : (
              <ul className="file-list">
                {files.map((f) => (
                  <li key={f.id} className="file-item">
                    <div className="file-info">
                      <span className="file-name" title={f.filename}>
                        {f.filename}
                      </span>
                      <span className={`file-status status-${f.status.toLowerCase()}`}>
                        {f.status === 'UPLOADED' && '已上传'}
                        {f.status === 'PROCESSING' && '处理中'}
                        {f.status === 'READY' && '可对话'}
                        {f.status === 'FAILED' && '失败'}
                      </span>
                    </div>
                    {f.status === 'UPLOADED' && (
                      <button
                        type="button"
                        className="file-process-btn"
                        onClick={() => handleProcess(f.id)}
                        disabled={processingId !== null}
                      >
                        {processingId === f.id ? '处理中…' : '处理'}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>

        <main className="dashboard-main">
          <div className="chat-panel">
            <div className="chat-file-bar">
              <label>
                选择文档进行对话：
                <select
                  value={selectedFileId ?? ''}
                  onChange={(e) => setSelectedFileId(e.target.value ? Number(e.target.value) : null)}
                  className="chat-select"
                >
                  <option value="">请选择</option>
                  {readyFiles.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.filename}
                    </option>
                  ))}
                </select>
              </label>
              {readyFiles.length === 0 && (
                <span className="chat-hint">请先在左侧上传并处理一个 PDF</span>
              )}
            </div>

            <div className="chat-messages">
              {messages.length === 0 && (
                <p className="chat-placeholder">选择文档后，在下方输入问题开始对话</p>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
                  <div className="chat-msg-content">{msg.content}</div>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="chat-citations">
                      {msg.citations.map((c, j) => (
                        <div key={j} className="chat-cite">
                          第 {c.page} 页：{c.snippet}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {sending && (
                <div className="chat-msg chat-msg-assistant">
                  <div className="chat-msg-content">思考中…</div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-row">
              <input
                type="text"
                placeholder={selectedFileId ? '输入问题…' : '请先选择文档'}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                disabled={!selectedFileId || sending}
                className="chat-input"
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={!selectedFileId || !input.trim() || sending}
                className="chat-send"
              >
                发送
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
