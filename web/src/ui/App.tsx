import React, { useCallback, useEffect, useRef, useState, memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, Check, Send, Plus, Sparkles, Loader2, RotateCcw, ThumbsUp, ThumbsDown, Building2 } from 'lucide-react'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  toolsUsed?: string[]
}

// Generate unique IDs
const genId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`

// Session management
function getStoredSessionId(): string | null {
  try { return localStorage.getItem('kahua.sessionId') } catch { return null }
}
function setStoredSessionId(id: string) {
  try { localStorage.setItem('kahua.sessionId', id) } catch {}
}
function generateSessionId(): string {
  return 'sess-' + Math.random().toString(36).slice(2, 10) + '-' + Date.now().toString(36)
}

// Copy button component for code blocks
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  
  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [text])
  
  return (
    <button onClick={handleCopy} className="copy-btn" title="Copy to clipboard">
      {copied ? <Check size={14} /> : <Copy size={14} />}
      <span style={{ marginLeft: 4 }}>{copied ? 'Copied!' : 'Copy'}</span>
    </button>
  )
}

// Custom code block renderer with copy button
const CodeBlock = memo(({ children, className }: { children: string; className?: string }) => {
  const language = className?.replace('language-', '') || ''
  
  return (
    <div className="code-block-wrapper">
      <CopyButton text={String(children).trim()} />
      {language && (
        <div style={{ 
          position: 'absolute', 
          top: 8, 
          left: 12, 
          fontSize: 11, 
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          {language}
        </div>
      )}
      <pre style={{ paddingTop: language ? 32 : 16 }}>
        <code className={className}>{children}</code>
      </pre>
    </div>
  )
})

// Table wrapper with copy functionality
const TableWrapper = memo(({ children }: { children: React.ReactNode }) => {
  const tableRef = useRef<HTMLDivElement>(null)
  const [copied, setCopied] = useState(false)
  
  const copyTable = useCallback(async () => {
    if (!tableRef.current) return
    const table = tableRef.current.querySelector('table')
    if (!table) return
    
    // Convert table to TSV for easy pasting into Excel
    const rows = Array.from(table.querySelectorAll('tr'))
    const tsv = rows.map(row => {
      const cells = Array.from(row.querySelectorAll('th, td'))
      return cells.map(cell => cell.textContent?.trim() || '').join('\t')
    }).join('\n')
    
    await navigator.clipboard.writeText(tsv)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [])
  
  return (
    <div ref={tableRef} style={{ position: 'relative', margin: '1em 0' }}>
      <button 
        onClick={copyTable}
        style={{
          position: 'absolute',
          top: -8,
          right: 0,
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-secondary)',
          padding: '4px 10px',
          borderRadius: 6,
          fontSize: 12,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          zIndex: 1
        }}
      >
        {copied ? <Check size={12} /> : <Copy size={12} />}
        {copied ? 'Copied!' : 'Copy table'}
      </button>
      <div style={{ overflowX: 'auto', marginTop: 8 }}>
        {children}
      </div>
    </div>
  )
})

// Message component with markdown rendering
const Message = memo(({ message, onRegenerate }: { 
  message: ChatMessage
  onRegenerate?: () => void 
}) => {
  const isUser = message.role === 'user'
  
  return (
    <div style={{
      padding: '24px 0',
      borderBottom: '1px solid var(--border-color)',
    }}>
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 24px' }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 12,
          marginBottom: 16
        }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 6,
            background: isUser ? 'var(--bg-tertiary)' : 'var(--accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            {isUser ? (
              <span style={{ fontSize: 14, fontWeight: 600 }}>Y</span>
            ) : (
              <Building2 size={18} color="white" />
            )}
          </div>
          <span style={{ fontWeight: 600, fontSize: 15 }}>
            {isUser ? 'You' : 'Kahua Assistant'}
          </span>
          {message.isStreaming && (
            <Loader2 size={16} className="thinking-indicator" style={{ marginLeft: 'auto' }} />
          )}
        </div>
        
        {/* Content */}
        <div className={`message-content ${message.isStreaming ? 'typing-cursor' : ''}`} style={{ marginLeft: 44 }}>
          {isUser ? (
            <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom code block rendering
                code({ node, className, children, ...props }) {
                  const isInline = !className && !String(children).includes('\n')
                  if (isInline) {
                    return <code {...props}>{children}</code>
                  }
                  return <CodeBlock className={className}>{String(children)}</CodeBlock>
                },
                // Custom table rendering with wrapper
                table({ children }) {
                  return (
                    <TableWrapper>
                      <table>{children}</table>
                    </TableWrapper>
                  )
                },
                // Links open in new tab
                a({ href, children }) {
                  const isReport = href?.includes('/reports/')
                  return (
                    <a 
                      href={href} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={isReport ? {
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        background: 'var(--accent)',
                        color: 'white',
                        padding: '10px 16px',
                        borderRadius: 8,
                        marginTop: 8,
                        fontWeight: 500,
                        textDecoration: 'none'
                      } : undefined}
                    >
                      {isReport && '📄 '}
                      {children}
                    </a>
                  )
                }
              }}
            >
              {message.content || ' '}
            </ReactMarkdown>
          )}
        </div>
        
        {/* Actions for assistant messages */}
        {!isUser && !message.isStreaming && message.content && (
          <div style={{ 
            marginLeft: 44, 
            marginTop: 16, 
            display: 'flex', 
            gap: 4 
          }}>
            <button className="icon-btn" title="Copy response" onClick={async () => {
              await navigator.clipboard.writeText(message.content)
            }}>
              <Copy size={16} />
            </button>
            <button className="icon-btn" title="Good response">
              <ThumbsUp size={16} />
            </button>
            <button className="icon-btn" title="Bad response">
              <ThumbsDown size={16} />
            </button>
            {onRegenerate && (
              <button className="icon-btn" title="Regenerate" onClick={onRegenerate}>
                <RotateCcw size={16} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
})

// Thinking/tool indicator
function ThinkingIndicator({ status }: { status: string }) {
  return (
    <div style={{
      padding: '24px 0',
      borderBottom: '1px solid var(--border-color)',
    }}>
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 6,
            background: 'var(--accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Building2 size={18} color="white" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Loader2 size={16} className="thinking-indicator" />
            <span style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{status}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Welcome screen
function WelcomeScreen() {
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center',
      height: '100%',
      padding: 24,
      textAlign: 'center'
    }}>
      <div style={{
        width: 64,
        height: 64,
        borderRadius: 16,
        background: 'linear-gradient(135deg, var(--accent) 0%, #0e8a6c 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 24
      }}>
        <Building2 size={32} color="white" />
      </div>
      <h1 style={{ 
        fontSize: 28, 
        fontWeight: 600, 
        marginBottom: 12,
        color: 'var(--text-primary)'
      }}>
        Kahua Assistant
      </h1>
      <p style={{ 
        color: 'var(--text-secondary)', 
        maxWidth: 480,
        lineHeight: 1.6,
        marginBottom: 32
      }}>
        Your AI-powered construction project analyst. Query projects, RFIs, submittals, 
        contracts, and generate professional reports.
      </p>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(2, 1fr)', 
        gap: 12,
        maxWidth: 520,
        width: '100%'
      }}>
        {[
          'What projects do I have?',
          'Show me all open RFIs',
          'Generate a contracts report',
          'List punch list items'
        ].map((prompt, i) => (
          <button
            key={i}
            className="data-card"
            style={{
              textAlign: 'left',
              cursor: 'pointer',
              border: '1px solid var(--border-color)',
              fontSize: 14,
              color: 'var(--text-secondary)'
            }}
          >
            <Sparkles size={14} style={{ marginRight: 8, color: 'var(--accent)' }} />
            {prompt}
          </button>
        ))}
      </div>
    </div>
  )
}

// Main App
export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(() => getStoredSessionId() || generateSessionId())
  const [busy, setBusy] = useState(false)
  const [thinkingStatus, setThinkingStatus] = useState<string | null>(null)
  
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  
  useEffect(() => { setStoredSessionId(sessionId) }, [sessionId])
  
  // Auto-resize textarea
  useEffect(() => {
    const textarea = inputRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
    }
  }, [input])
  
  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
    }, 50)
  }, [])
  
  const newSession = useCallback(() => {
    const next = generateSessionId()
    setSessionId(next)
    setMessages([])
  }, [])
  
  const handleSend = useCallback(async () => {
    if (!input.trim() || busy) return
    
    const userMsg: ChatMessage = { id: genId(), role: 'user', content: input.trim() }
    const assistantMsg: ChatMessage = { id: genId(), role: 'assistant', content: '', isStreaming: true }
    
    setMessages(prev => [...prev, userMsg, assistantMsg])
    setInput('')
    setBusy(true)
    setThinkingStatus('Thinking...')
    scrollToBottom()
    
    try {
      const resp = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, session_id: sessionId })
      })
      
      if (!resp.ok || !resp.body) {
        throw new Error(`HTTP ${resp.status}`)
      }
      
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      
      while (true) {
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
            setThinkingStatus(null)
            setMessages(prev => {
              const copy = [...prev]
              const last = copy[copy.length - 1]
              if (last?.role === 'assistant') {
                copy[copy.length - 1] = { ...last, content: last.content + evt.content }
              }
              return copy
            })
            scrollToBottom()
          } else if (evt.type === 'item' && evt.item_type === 'tool_call_item') {
            setThinkingStatus('Querying Kahua...')
          } else if (evt.type === 'error') {
            setMessages(prev => {
              const copy = [...prev]
              const last = copy[copy.length - 1]
              if (last?.role === 'assistant') {
                copy[copy.length - 1] = { ...last, content: `Error: ${evt.message}`, isStreaming: false }
              }
              return copy
            })
          } else if (evt.type === 'done') {
            setMessages(prev => {
              const copy = [...prev]
              const last = copy[copy.length - 1]
              if (last?.role === 'assistant') {
                copy[copy.length - 1] = { ...last, isStreaming: false }
              }
              return copy
            })
          }
        }
      }
    } catch (e: any) {
      setMessages(prev => {
        const copy = [...prev]
        const last = copy[copy.length - 1]
        if (last?.role === 'assistant') {
          copy[copy.length - 1] = { ...last, content: `Error: ${e?.message || e}`, isStreaming: false }
        }
        return copy
      })
    } finally {
      setBusy(false)
      setThinkingStatus(null)
      setMessages(prev => {
        const copy = [...prev]
        const last = copy[copy.length - 1]
        if (last?.role === 'assistant' && last.isStreaming) {
          copy[copy.length - 1] = { ...last, isStreaming: false }
        }
        return copy
      })
      scrollToBottom()
    }
  }, [input, busy, sessionId, scrollToBottom])
  
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])
  
  return (
    <div style={{ 
      display: 'grid', 
      gridTemplateRows: 'auto 1fr auto', 
      height: '100vh',
      background: 'var(--bg-primary)'
    }}>
      {/* Header */}
      <header style={{ 
        padding: '12px 24px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        background: 'var(--bg-secondary)'
      }}>
        <Building2 size={24} color="var(--accent)" />
        <span style={{ fontWeight: 600, fontSize: 16 }}>Kahua Assistant</span>
        
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Session: {sessionId.slice(0, 12)}...
          </span>
          <button className="btn-secondary" onClick={newSession}>
            <Plus size={14} style={{ marginRight: 6 }} />
            New Chat
          </button>
        </div>
      </header>
      
      {/* Messages */}
      <div 
        ref={scrollRef} 
        style={{ 
          overflow: 'auto',
          background: 'var(--bg-primary)'
        }}
      >
        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          <>
            {messages.filter(m => !m.isStreaming || m.content).map(msg => (
              <Message key={msg.id} message={msg} />
            ))}
            {thinkingStatus && <ThinkingIndicator status={thinkingStatus} />}
          </>
        )}
      </div>
      
      {/* Input */}
      <footer style={{ 
        padding: '16px 24px 24px',
        background: 'var(--bg-primary)'
      }}>
        <div style={{ 
          maxWidth: 800, 
          margin: '0 auto',
          position: 'relative'
        }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your projects, RFIs, contracts..."
            rows={1}
            className="chat-input"
            style={{ paddingRight: 52 }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || busy}
            style={{
              position: 'absolute',
              right: 8,
              bottom: 8,
              background: input.trim() && !busy ? 'var(--accent)' : 'var(--bg-tertiary)',
              border: 'none',
              borderRadius: 8,
              padding: 8,
              cursor: input.trim() && !busy ? 'pointer' : 'not-allowed',
              transition: 'all 0.15s ease'
            }}
          >
            {busy ? (
              <Loader2 size={18} color="var(--text-muted)" className="thinking-indicator" />
            ) : (
              <Send size={18} color={input.trim() ? 'white' : 'var(--text-muted)'} />
            )}
          </button>
        </div>
        <p style={{ 
          textAlign: 'center', 
          fontSize: 12, 
          color: 'var(--text-muted)',
          marginTop: 12
        }}>
          Press Enter to send • Shift+Enter for new line
        </p>
      </footer>
    </div>
  )
}
