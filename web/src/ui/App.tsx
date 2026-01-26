import React, { useCallback, useEffect, useRef, useState, memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, Check, Send, Plus, Sparkles, Loader2, RotateCcw, ThumbsUp, ThumbsDown, Building2, FileText, ChevronRight, X, Search, Tag, FolderOpen } from 'lucide-react'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  toolsUsed?: string[]
}

// Template types
type ReportTemplate = {
  id: string
  name: string
  description: string
  category: string
  tags: string[]
  is_public: boolean
  created_at: string
  updated_at: string
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

// Category config for templates
const CATEGORY_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  cost: { icon: '💰', color: '#38a169', label: 'Cost & Contracts' },
  field: { icon: '🏗️', color: '#3182ce', label: 'Field Operations' },
  executive: { icon: '📊', color: '#805ad5', label: 'Executive' },
  custom: { icon: '✨', color: '#dd6b20', label: 'Custom' },
}

// Template Library Sidebar
function TemplateLibrary({ 
  isOpen, 
  onClose, 
  onSelectTemplate 
}: { 
  isOpen: boolean
  onClose: () => void
  onSelectTemplate: (template: ReportTemplate) => void
}) {
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  
  // Fetch templates
  useEffect(() => {
    if (isOpen) {
      setLoading(true)
      fetch('/api/templates')
        .then(r => r.json())
        .then(data => {
          setTemplates(data.templates || [])
          setLoading(false)
        })
        .catch(() => setLoading(false))
    }
  }, [isOpen])
  
  // Filter templates
  const filtered = templates.filter(t => {
    const matchesSearch = !search || 
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = !selectedCategory || t.category === selectedCategory
    return matchesSearch && matchesCategory
  })
  
  // Group by category
  const grouped = filtered.reduce((acc, t) => {
    if (!acc[t.category]) acc[t.category] = []
    acc[t.category].push(t)
    return acc
  }, {} as Record<string, ReportTemplate[]>)
  
  if (!isOpen) return null
  
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: 380,
      background: 'var(--bg-secondary)',
      borderLeft: '1px solid var(--border-color)',
      zIndex: 100,
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '-4px 0 20px rgba(0,0,0,0.3)'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        gap: 12
      }}>
        <FileText size={20} style={{ color: 'var(--accent)' }} />
        <h2 style={{ flex: 1, fontSize: 16, fontWeight: 600, margin: 0 }}>Report Templates</h2>
        <button onClick={onClose} className="icon-btn">
          <X size={18} />
        </button>
      </div>
      
      {/* Search */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ position: 'relative' }}>
          <Search size={16} style={{
            position: 'absolute',
            left: 12,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-muted)'
          }} />
          <input
            type="text"
            placeholder="Search templates..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px 10px 38px',
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border-color)',
              borderRadius: 8,
              color: 'var(--text-primary)',
              fontSize: 14
            }}
          />
        </div>
        
        {/* Category filters */}
        <div style={{ display: 'flex', gap: 6, marginTop: 12, flexWrap: 'wrap' }}>
          <button
            onClick={() => setSelectedCategory(null)}
            style={{
              padding: '6px 12px',
              borderRadius: 16,
              border: '1px solid var(--border-color)',
              background: !selectedCategory ? 'var(--accent)' : 'transparent',
              color: !selectedCategory ? 'white' : 'var(--text-secondary)',
              fontSize: 12,
              cursor: 'pointer'
            }}
          >
            All
          </button>
          {Object.entries(CATEGORY_CONFIG).map(([key, { icon, label }]) => (
            <button
              key={key}
              onClick={() => setSelectedCategory(key === selectedCategory ? null : key)}
              style={{
                padding: '6px 12px',
                borderRadius: 16,
                border: '1px solid var(--border-color)',
                background: key === selectedCategory ? 'var(--accent)' : 'transparent',
                color: key === selectedCategory ? 'white' : 'var(--text-secondary)',
                fontSize: 12,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4
              }}
            >
              <span>{icon}</span> {label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Template list */}
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 16px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
            <Loader2 size={24} className="thinking-indicator" />
            <p style={{ marginTop: 12 }}>Loading templates...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
            <FolderOpen size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
            <p>No templates found</p>
          </div>
        ) : (
          Object.entries(grouped).map(([category, categoryTemplates]) => (
            <div key={category} style={{ marginBottom: 20 }}>
              <h3 style={{
                fontSize: 11,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--text-muted)',
                marginBottom: 8,
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}>
                <span>{CATEGORY_CONFIG[category]?.icon || '📄'}</span>
                {CATEGORY_CONFIG[category]?.label || category}
              </h3>
              {categoryTemplates.map(template => (
                <button
                  key={template.id}
                  onClick={() => onSelectTemplate(template)}
                  style={{
                    width: '100%',
                    padding: '14px 16px',
                    marginBottom: 8,
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 10,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'var(--accent)'
                    e.currentTarget.style.background = 'var(--bg-primary)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'var(--border-color)'
                    e.currentTarget.style.background = 'var(--bg-tertiary)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{
                        fontWeight: 500,
                        fontSize: 14,
                        color: 'var(--text-primary)',
                        marginBottom: 4
                      }}>
                        {template.name}
                      </div>
                      <div style={{
                        fontSize: 12,
                        color: 'var(--text-muted)',
                        lineHeight: 1.4
                      }}>
                        {template.description.length > 100 
                          ? template.description.slice(0, 100) + '...' 
                          : template.description}
                      </div>
                      {template.tags?.length > 0 && (
                        <div style={{ display: 'flex', gap: 4, marginTop: 8, flexWrap: 'wrap' }}>
                          {template.tags.slice(0, 3).map(tag => (
                            <span key={tag} style={{
                              padding: '2px 8px',
                              background: 'var(--bg-primary)',
                              borderRadius: 4,
                              fontSize: 10,
                              color: 'var(--text-muted)'
                            }}>
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <ChevronRight size={16} style={{ color: 'var(--text-muted)', flexShrink: 0, marginTop: 2 }} />
                  </div>
                </button>
              ))}
            </div>
          ))
        )}
      </div>
      
      {/* Footer */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--border-color)',
        background: 'var(--bg-tertiary)'
      }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>
          Select a template to generate a report
        </p>
      </div>
    </div>
  )
}

// Welcome screen
function WelcomeScreen({ onQuickAction }: { onQuickAction: (prompt: string) => void }) {
  const quickActions = [
    { prompt: 'What projects do I have?', icon: '📁', desc: 'List all projects' },
    { prompt: 'Show me all open RFIs', icon: '📋', desc: 'Open RFI status' },
    { prompt: 'Generate a contracts report', icon: '📊', desc: 'Contract summary' },
    { prompt: 'List punch list items', icon: '✅', desc: 'Punch list review' },
    { prompt: 'What data exists in my environment?', icon: '🔍', desc: 'Data discovery' },
    { prompt: 'Show me overdue items', icon: '⚠️', desc: 'Risk overview' },
  ]
  
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
        maxWidth: 560,
        width: '100%'
      }}>
        {quickActions.map((action, i) => (
          <button
            key={i}
            className="data-card"
            onClick={() => onQuickAction(action.prompt)}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 12,
              textAlign: 'left',
              cursor: 'pointer',
              border: '1px solid var(--border-color)',
              fontSize: 14,
              color: 'var(--text-secondary)',
              lineHeight: 1.4,
              padding: '14px 16px',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = 'var(--accent)'
              e.currentTarget.style.background = 'var(--bg-tertiary)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'var(--border-color)'
              e.currentTarget.style.background = ''
            }}
          >
            <span style={{ fontSize: 20 }}>{action.icon}</span>
            <div>
              <div style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>
                {action.desc}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                "{action.prompt}"
              </div>
            </div>
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
  const [showTemplates, setShowTemplates] = useState(false)
  
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
  
  // Core send function - accepts optional prompt for quick actions
  const sendMessage = useCallback(async (messageText: string) => {
    if (!messageText.trim() || busy) return
    
    const userMsg: ChatMessage = { id: genId(), role: 'user', content: messageText.trim() }
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
  }, [busy, sessionId, scrollToBottom])
  
  // Wrapper for input field send
  const handleSend = useCallback(() => {
    sendMessage(input)
  }, [input, sendMessage])
  
  // Handler for quick actions
  const handleQuickAction = useCallback((prompt: string) => {
    sendMessage(prompt)
  }, [sendMessage])
  
  // Handler for template selection
  const handleTemplateSelect = useCallback((template: ReportTemplate) => {
    setShowTemplates(false)
    const prompt = `Generate a "${template.name}" report using the template. Template description: ${template.description}`
    sendMessage(prompt)
  }, [sendMessage])
  
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
      {/* Template Library Sidebar */}
      <TemplateLibrary 
        isOpen={showTemplates} 
        onClose={() => setShowTemplates(false)}
        onSelectTemplate={handleTemplateSelect}
      />
      
      {/* Header */}
      <header style={{ 
        padding: '14px 24px',
        borderBottom: '1px solid #333',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        background: '#1a1a1a'
      }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: 'var(--accent)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Building2 size={18} color="white" />
        </div>
        <span style={{ fontWeight: 600, fontSize: 15 }}>Kahua Assistant</span>
        
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          <button 
            className="btn-secondary" 
            onClick={() => setShowTemplates(true)}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <FileText size={14} />
            Templates
          </button>
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
          <WelcomeScreen onQuickAction={handleQuickAction} />
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
        background: 'var(--bg-primary)',
        borderTop: '1px solid #222'
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
