/**
 * Conversation History Management
 * Persists chat sessions to localStorage with search and organization
 */

import React, { useState, useEffect, useCallback, memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  MessageSquare, Clock, Trash2, Search, ChevronRight, 
  Star, StarOff, MoreHorizontal, X, Plus
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

// Types
export interface ChatSession {
  id: string
  title: string
  preview: string
  messages: Array<{
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: number
  }>
  createdAt: number
  updatedAt: number
  starred: boolean
}

// Storage keys
const STORAGE_KEY = 'kahua.chatHistory'
const MAX_SESSIONS = 50

// ============== Storage Functions ==============

export function loadChatHistory(): ChatSession[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function saveChatHistory(sessions: ChatSession[]): void {
  try {
    // Keep only the most recent sessions
    const trimmed = sessions.slice(0, MAX_SESSIONS)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed))
  } catch {
    console.warn('Failed to save chat history')
  }
}

export function saveSession(session: ChatSession): void {
  const history = loadChatHistory()
  const existingIdx = history.findIndex(s => s.id === session.id)
  
  if (existingIdx >= 0) {
    history[existingIdx] = session
  } else {
    history.unshift(session)
  }
  
  saveChatHistory(history)
}

export function deleteSession(sessionId: string): void {
  const history = loadChatHistory()
  const filtered = history.filter(s => s.id !== sessionId)
  saveChatHistory(filtered)
}

export function generateTitle(messages: Array<{ role: string; content: string }>): string {
  // Use the first user message as the title
  const firstUserMsg = messages.find(m => m.role === 'user')
  if (!firstUserMsg) return 'New Chat'
  
  const content = firstUserMsg.content.trim()
  // Truncate and clean up
  if (content.length <= 40) return content
  return content.slice(0, 40).trim() + '...'
}

// ============== History Sidebar Component ==============

interface HistorySidebarProps {
  isOpen: boolean
  onClose: () => void
  sessions: ChatSession[]
  currentSessionId: string
  onSelectSession: (session: ChatSession) => void
  onNewChat: () => void
  onDeleteSession: (sessionId: string) => void
}

export const HistorySidebar = memo(({ 
  isOpen, 
  onClose, 
  sessions: externalSessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession
}: HistorySidebarProps) => {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [search, setSearch] = useState('')
  const [showStarredOnly, setShowStarredOnly] = useState(false)
  
  // Sync with external sessions when they change or sidebar opens
  useEffect(() => {
    if (isOpen) {
      setSessions(externalSessions)
    }
  }, [isOpen, externalSessions])
  
  // Filter sessions
  const filtered = sessions.filter(s => {
    if (showStarredOnly && !s.starred) return false
    if (!search) return true
    const searchLower = search.toLowerCase()
    return s.title.toLowerCase().includes(searchLower) ||
           s.preview.toLowerCase().includes(searchLower)
  })
  
  // Group by date
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const lastWeek = new Date(today)
  lastWeek.setDate(lastWeek.getDate() - 7)
  
  const grouped = {
    today: filtered.filter(s => s.updatedAt >= today.getTime()),
    yesterday: filtered.filter(s => s.updatedAt >= yesterday.getTime() && s.updatedAt < today.getTime()),
    thisWeek: filtered.filter(s => s.updatedAt >= lastWeek.getTime() && s.updatedAt < yesterday.getTime()),
    older: filtered.filter(s => s.updatedAt < lastWeek.getTime())
  }
  
  const handleDelete = useCallback((e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    onDeleteSession(sessionId)
  }, [onDeleteSession])
  
  const handleToggleStar = useCallback((e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation()
    const updated = { ...session, starred: !session.starred }
    saveSession(updated)
    setSessions(loadChatHistory())
  }, [])
  
  if (!isOpen) return null
  
  const SessionItem = ({ session }: { session: ChatSession }) => {
    const isActive = session.id === currentSessionId
    const [showActions, setShowActions] = useState(false)
    
    return (
      <motion.button
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        onClick={() => onSelectSession(session)}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 12,
          padding: '12px 14px',
          background: isActive ? 'var(--bg-tertiary)' : 'transparent',
          border: 'none',
          borderRadius: 8,
          cursor: 'pointer',
          textAlign: 'left',
          marginBottom: 4,
          position: 'relative'
        }}
      >
        <MessageSquare 
          size={16} 
          style={{ 
            color: isActive ? 'var(--accent)' : 'var(--text-muted)',
            marginTop: 2,
            flexShrink: 0
          }} 
        />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 14,
            fontWeight: isActive ? 600 : 400,
            color: 'var(--text-primary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            paddingRight: showActions ? 60 : 0
          }}>
            {session.starred && <Star size={12} style={{ color: '#f59e0b', marginRight: 6 }} />}
            {session.title}
          </div>
          <div style={{
            fontSize: 12,
            color: 'var(--text-muted)',
            marginTop: 2
          }}>
            {formatDistanceToNow(session.updatedAt, { addSuffix: true })}
          </div>
        </div>
        
        <AnimatePresence>
          {showActions && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute',
                right: 8,
                top: '50%',
                transform: 'translateY(-50%)',
                display: 'flex',
                gap: 4
              }}
            >
              <button
                onClick={(e) => handleToggleStar(e, session)}
                className="icon-btn"
                title={session.starred ? 'Unstar' : 'Star'}
                style={{ padding: 4 }}
              >
                {session.starred ? <StarOff size={14} /> : <Star size={14} />}
              </button>
              <button
                onClick={(e) => handleDelete(e, session.id)}
                className="icon-btn"
                title="Delete"
                style={{ padding: 4, color: '#ef4444' }}
              >
                <Trash2 size={14} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    )
  }
  
  const SectionHeader = ({ title, count }: { title: string; count: number }) => (
    count > 0 ? (
      <div style={{
        fontSize: 11,
        fontWeight: 600,
        color: 'var(--text-muted)',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        padding: '12px 14px 6px',
        marginTop: 8
      }}>
        {title}
      </div>
    ) : null
  )
  
  return (
    <motion.div
      initial={{ x: -300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -300, opacity: 0 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
        width: 300,
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-color)',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '4px 0 20px rgba(0,0,0,0.3)'
      }}
    >
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        gap: 12
      }}>
        <Clock size={20} style={{ color: 'var(--accent)' }} />
        <h2 style={{ flex: 1, fontSize: 16, fontWeight: 600, margin: 0 }}>History</h2>
        <button onClick={onClose} className="icon-btn">
          <X size={18} />
        </button>
      </div>
      
      {/* New Chat Button */}
      <div style={{ padding: '12px 12px 0' }}>
        <button
          onClick={() => { onNewChat(); onClose(); }}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            padding: '10px 16px',
            background: 'var(--accent)',
            border: 'none',
            borderRadius: 8,
            color: 'white',
            fontWeight: 500,
            cursor: 'pointer'
          }}
        >
          <Plus size={16} />
          New Chat
        </button>
      </div>
      
      {/* Search */}
      <div style={{ padding: '12px' }}>
        <div style={{ position: 'relative' }}>
          <Search size={14} style={{
            position: 'absolute',
            left: 10,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-muted)'
          }} />
          <input
            type="text"
            placeholder="Search conversations..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 10px 8px 32px',
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border-color)',
              borderRadius: 6,
              color: 'var(--text-primary)',
              fontSize: 13
            }}
          />
        </div>
        
        {/* Filter toggle */}
        <button
          onClick={() => setShowStarredOnly(!showStarredOnly)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 10px',
            marginTop: 8,
            background: showStarredOnly ? 'rgba(245, 158, 11, 0.15)' : 'transparent',
            border: '1px solid var(--border-color)',
            borderRadius: 16,
            fontSize: 12,
            color: showStarredOnly ? '#f59e0b' : 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          <Star size={12} />
          Starred only
        </button>
      </div>
      
      {/* Session List */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 8px 12px' }}>
        {filtered.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: 40, 
            color: 'var(--text-muted)' 
          }}>
            <MessageSquare size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
            <p>No conversations yet</p>
          </div>
        ) : (
          <>
            <SectionHeader title="Today" count={grouped.today.length} />
            {grouped.today.map(s => <SessionItem key={s.id} session={s} />)}
            
            <SectionHeader title="Yesterday" count={grouped.yesterday.length} />
            {grouped.yesterday.map(s => <SessionItem key={s.id} session={s} />)}
            
            <SectionHeader title="This Week" count={grouped.thisWeek.length} />
            {grouped.thisWeek.map(s => <SessionItem key={s.id} session={s} />)}
            
            <SectionHeader title="Older" count={grouped.older.length} />
            {grouped.older.map(s => <SessionItem key={s.id} session={s} />)}
          </>
        )}
      </div>
    </motion.div>
  )
})
