import React, { useEffect, useMemo, useRef, useState } from 'react'

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

// Convert URLs in text to clickable links
function linkifyText(text: string): React.ReactNode[] {
  const urlRegex = /(https?:\/\/[^\s<>"\)]+)/g
  const parts = text.split(urlRegex)
  return parts.map((part, i) => {
    if (urlRegex.test(part)) {
      // Reset lastIndex since test() advances it
      urlRegex.lastIndex = 0
      
      // Determine link label based on file type
      let label = part
      if (part.includes('/reports/')) {
        if (part.endsWith('.docx')) {
          label = '📄 Download Word Document'
        } else if (part.endsWith('.pdf')) {
          label = '📄 Download PDF'
        } else {
          label = '📄 Download Report'
        }
      }
      
      return (
        <a 
          key={i} 
          href={part} 
          target="_blank" 
          rel="noopener noreferrer"
          style={{ 
            color: '#2563eb', 
            textDecoration: 'none',
            background: '#eff6ff',
            padding: '6px 12px',
            borderRadius: '6px',
            display: 'inline-block',
            marginTop: '8px',
            fontWeight: 500
          }}
        >
          {label}
        </a>
      )
    }
    return part
  })
}

function getStoredSessionId(): string | null {
  try {
    return localStorage.getItem('kahua.sessionId')
  } catch {
    return null
  }
}

function setStoredSessionId(id: string) {
  try {
    localStorage.setItem('kahua.sessionId', id)
  } catch {}
}

function generateSessionId(): string {
  // Simple RFC4122-ish random id; good enough for client-side session key
  return 'sess-' + Math.random().toString(36).slice(2, 10) + '-' + Date.now().toString(36)
}

async function sendMessage(message: string, sessionId?: string): Promise<string> {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId ?? 'web' })
  })
  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`
    try {
      const err = await resp.json()
      if (err?.detail) detail += `: ${err.detail}`
    } catch {
      const text = await resp.text()
      if (text) detail += `: ${text}`
    }
    throw new Error(detail)
  }
  const data = await resp.json()
  return String(data.final_output ?? '')
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string>(() => getStoredSessionId() || generateSessionId())
  useEffect(() => {
    setStoredSessionId(sessionId)
  }, [sessionId])

  function newSession() {
    const next = generateSessionId()
    setSessionId(next)
    setMessages([])
  }

  const [busy, setBusy] = useState(false)
  const scroller = useRef<HTMLDivElement>(null)

  const canSend = input.trim().length > 0 && !busy

  async function handleSend() {
    if (!canSend) return
    const userMsg: ChatMessage = { role: 'user', content: input.trim() }
    const start: ChatMessage[] = [...messages, userMsg, { role: 'assistant', content: '' }]
    const assistantIndex = start.length - 1
    setMessages(start)
    setInput('')
    setBusy(true)
    try {
      const resp = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, session_id: sessionId ?? 'web' })
      })
      if (!resp.ok || !resp.body) {
        let detail = `HTTP ${resp.status}`
        try {
          const err = await resp.json()
          if (err?.detail) detail += `: ${err.detail}`
        } catch {}
        throw new Error(detail)
      }
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      for (;;) {
        const { value, done } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const parts = buf.split('\n\n')
        buf = parts.pop() || ''
        for (const chunk of parts) {
          if (!chunk.startsWith('data:')) continue
          const raw = chunk.slice(5).trim()
          if (!raw) continue
          let evt: any
          try { evt = JSON.parse(raw) } catch { continue }
          if (evt.type === 'delta' && typeof evt.content === 'string') {
            setMessages(prev => {
              const copy = prev.slice()
              const curr = copy[assistantIndex]
              copy[assistantIndex] = { ...curr, content: (curr?.content || '') + evt.content }
              return copy
            })
            // auto-scroll as content streams
            scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: 'smooth' })
          } else if (evt.type === 'error') {
            const msg = typeof evt.message === 'string' ? evt.message : 'Unknown error'
            setMessages(prev => {
              const copy = prev.slice()
              copy[assistantIndex] = { role: 'assistant', content: `Error: ${msg}` }
              return copy
            })
          } else if (evt.type === 'done') {
            // stream completed
          }
        }
      }
    } catch (e: any) {
      setMessages(prev => {
        const copy = prev.slice()
        copy[assistantIndex] = { role: 'assistant', content: `Error: ${e?.message || e}` }
        return copy
      })
    } finally {
      setBusy(false)
      setTimeout(() => scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: 'smooth' }), 50)
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{display:'grid', gridTemplateRows:'auto 1fr auto', height:'100vh'}}>
      <header style={{padding:'12px 16px', borderBottom:'1px solid #eee', display:'flex', gap:12, alignItems:'center'}}>
        <strong>Kahua Chat</strong>
        <div style={{marginLeft:'auto', display:'flex', gap:8, alignItems:'center'}}>
          <label style={{fontSize:12, color:'#666'}}>Session</label>
          <input value={sessionId} onChange={e => setSessionId(e.target.value)} style={{padding:'6px 8px'}} />
          <button onClick={newSession} title="Start a new session">New</button>
        </div>
      </header>
      <div ref={scroller} style={{overflow:'auto', padding:16, background:'#fafafa'}}>
        {messages.map((m, i) => (
          <div key={i} style={{maxWidth:720, margin:'0 auto 12px auto'}}>
            <div style={{
              background: m.role === 'user' ? '#fff' : '#f0f7ff',
              border:'1px solid #e2e8f0', borderRadius:8, padding:'10px 12px'
            }}>
              <div style={{fontSize:12, color:'#64748b', marginBottom:6}}>{m.role}</div>
              <div style={{whiteSpace:'pre-wrap'}}>{linkifyText(m.content)}</div>
            </div>
          </div>
        ))}
        {messages.length === 0 && (
          <div style={{textAlign:'center', color:'#94a3b8', marginTop:48}}>Start chatting with your Kahua agent…</div>
        )}
      </div>
      <footer style={{padding:12, borderTop:'1px solid #eee', background:'#fff'}}>
        <div style={{maxWidth:960, margin:'0 auto', display:'grid', gridTemplateColumns:'1fr auto', gap:8}}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Type a message..."
            rows={3}
            style={{resize:'none', padding:12, border:'1px solid #e2e8f0', borderRadius:8}}
          />
          <button onClick={handleSend} disabled={!canSend} style={{padding:'0 16px', borderRadius:8}}>
            {busy ? 'Sending…' : 'Send'}
          </button>
        </div>
        <div style={{maxWidth:960, margin:'6px auto 0 auto', fontSize:12, color:'#64748b'}}>
          Press Enter to send, Shift+Enter for newline
        </div>
      </footer>
    </div>
  )
}


