/**
 * Command Palette - Spotlight-style quick action interface
 * Inspired by VS Code, Raycast, and Linear
 */

import React, { useState, useEffect, useCallback, useRef, memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, FileText, FolderOpen, Building2, ClipboardList, 
  DollarSign, AlertTriangle, BarChart3, Plus, History,
  Command, ArrowRight, Sparkles
} from 'lucide-react'

interface CommandItem {
  id: string
  label: string
  description?: string
  icon: React.ReactNode
  category: 'query' | 'report' | 'action' | 'navigation'
  action: () => void
  keywords?: string[]
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  onQuickAction: (prompt: string) => void
  onNewChat: () => void
  onShowHistory: () => void
  onShowTemplates: () => void
}

const CATEGORIES = {
  query: { label: 'Queries', color: '#3182ce' },
  report: { label: 'Reports', color: '#38a169' },
  action: { label: 'Actions', color: '#805ad5' },
  navigation: { label: 'Navigation', color: '#dd6b20' }
}

export const CommandPalette = memo(({
  isOpen,
  onClose,
  onQuickAction,
  onNewChat,
  onShowHistory,
  onShowTemplates
}: CommandPaletteProps) => {
  const [search, setSearch] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  // Define all commands
  const commands: CommandItem[] = [
    // Queries
    {
      id: 'list-projects',
      label: 'List all projects',
      description: 'See all projects in your environment',
      icon: <FolderOpen size={18} />,
      category: 'query',
      action: () => onQuickAction('What projects do I have?'),
      keywords: ['projects', 'list', 'all', 'show']
    },
    {
      id: 'open-rfis',
      label: 'Show open RFIs',
      description: 'View all RFIs awaiting response',
      icon: <ClipboardList size={18} />,
      category: 'query',
      action: () => onQuickAction('Show me all open RFIs'),
      keywords: ['rfi', 'open', 'pending', 'requests']
    },
    {
      id: 'contracts',
      label: 'View contracts',
      description: 'See contract summaries and values',
      icon: <DollarSign size={18} />,
      category: 'query',
      action: () => onQuickAction('Show me all contracts'),
      keywords: ['contracts', 'cost', 'budget', 'money']
    },
    {
      id: 'punch-list',
      label: 'Punch list items',
      description: 'Review outstanding punch list items',
      icon: <ClipboardList size={18} />,
      category: 'query',
      action: () => onQuickAction('List all punch list items'),
      keywords: ['punch', 'list', 'items', 'closeout']
    },
    {
      id: 'overdue',
      label: 'Overdue items',
      description: 'Find items past their due date',
      icon: <AlertTriangle size={18} />,
      category: 'query',
      action: () => onQuickAction('Show me all overdue items'),
      keywords: ['overdue', 'late', 'past due', 'risk']
    },
    {
      id: 'discover',
      label: 'Discover my data',
      description: 'See what data exists in your environment',
      icon: <Search size={18} />,
      category: 'query',
      action: () => onQuickAction('What data exists in my environment?'),
      keywords: ['discover', 'explore', 'data', 'available']
    },
    
    // Reports
    {
      id: 'rfi-report',
      label: 'Generate RFI Status Report',
      description: 'Professional RFI tracking report',
      icon: <BarChart3 size={18} />,
      category: 'report',
      action: () => onQuickAction('Generate an RFI Status Report'),
      keywords: ['report', 'rfi', 'status', 'generate']
    },
    {
      id: 'contract-report',
      label: 'Generate Contract Summary',
      description: 'Cost and contracts overview',
      icon: <BarChart3 size={18} />,
      category: 'report',
      action: () => onQuickAction('Generate a Contract Summary Report'),
      keywords: ['report', 'contract', 'cost', 'summary']
    },
    {
      id: 'punch-report',
      label: 'Generate Punch List Report',
      description: 'Closeout progress by location/trade',
      icon: <BarChart3 size={18} />,
      category: 'report',
      action: () => onQuickAction('Generate a Punch List Closeout Report'),
      keywords: ['report', 'punch', 'closeout', 'generate']
    },
    
    // Actions
    {
      id: 'new-chat',
      label: 'New conversation',
      description: 'Start a fresh chat session',
      icon: <Plus size={18} />,
      category: 'action',
      action: () => { onNewChat(); onClose(); },
      keywords: ['new', 'chat', 'conversation', 'fresh', 'start']
    },
    {
      id: 'templates',
      label: 'Browse templates',
      description: 'View and select report templates',
      icon: <FileText size={18} />,
      category: 'action',
      action: () => { onShowTemplates(); onClose(); },
      keywords: ['templates', 'browse', 'reports', 'library']
    },
    
    // Navigation
    {
      id: 'history',
      label: 'Chat history',
      description: 'View past conversations',
      icon: <History size={18} />,
      category: 'navigation',
      action: () => { onShowHistory(); onClose(); },
      keywords: ['history', 'past', 'previous', 'conversations']
    }
  ]

  // Filter commands based on search
  const filtered = search.trim()
    ? commands.filter(cmd => {
        const searchLower = search.toLowerCase()
        return (
          cmd.label.toLowerCase().includes(searchLower) ||
          cmd.description?.toLowerCase().includes(searchLower) ||
          cmd.keywords?.some(k => k.includes(searchLower))
        )
      })
    : commands

  // Group by category
  const grouped = filtered.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = []
    acc[cmd.category].push(cmd)
    return acc
  }, {} as Record<string, CommandItem[]>)

  // Flatten for keyboard navigation
  const flatList = Object.values(grouped).flat()

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
      setSearch('')
      setSelectedIndex(0)
    }
  }, [isOpen])

  // Reset selection when search changes
  useEffect(() => {
    setSelectedIndex(0)
  }, [search])

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => Math.min(prev + 1, flatList.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (flatList[selectedIndex]) {
          flatList[selectedIndex].action()
          onClose()
        }
        break
      case 'Escape':
        e.preventDefault()
        onClose()
        break
    }
  }, [flatList, selectedIndex, onClose])

  // Scroll selected item into view
  useEffect(() => {
    const selectedEl = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`)
    selectedEl?.scrollIntoView({ block: 'nearest' })
  }, [selectedIndex])

  if (!isOpen) return null

  let itemIndex = -1

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.6)',
              backdropFilter: 'blur(4px)',
              zIndex: 200
            }}
          />
          
          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'fixed',
              top: '15%',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '100%',
              maxWidth: 560,
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 16,
              boxShadow: '0 24px 60px rgba(0,0,0,0.5)',
              zIndex: 201,
              overflow: 'hidden'
            }}
          >
            {/* Search Input */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '16px 20px',
              borderBottom: '1px solid var(--border-color)'
            }}>
              <Search size={20} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
              <input
                ref={inputRef}
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search commands..."
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  fontSize: 16,
                  color: 'var(--text-primary)'
                }}
              />
              <div style={{
                padding: '4px 8px',
                background: 'var(--bg-tertiary)',
                borderRadius: 6,
                fontSize: 11,
                color: 'var(--text-muted)'
              }}>
                ESC to close
              </div>
            </div>

            {/* Results */}
            <div
              ref={listRef}
              style={{
                maxHeight: 400,
                overflowY: 'auto',
                padding: '8px 0'
              }}
            >
              {flatList.length === 0 ? (
                <div style={{
                  padding: '32px 20px',
                  textAlign: 'center',
                  color: 'var(--text-muted)'
                }}>
                  <Sparkles size={24} style={{ marginBottom: 8, opacity: 0.5 }} />
                  <p>No commands found for "{search}"</p>
                  <p style={{ fontSize: 13, marginTop: 4 }}>Try a different search term</p>
                </div>
              ) : (
                Object.entries(grouped).map(([category, items]) => (
                  <div key={category}>
                    <div style={{
                      padding: '8px 20px 4px',
                      fontSize: 11,
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      color: CATEGORIES[category as keyof typeof CATEGORIES]?.color || 'var(--text-muted)'
                    }}>
                      {CATEGORIES[category as keyof typeof CATEGORIES]?.label || category}
                    </div>
                    {items.map((cmd) => {
                      itemIndex++
                      const isSelected = itemIndex === selectedIndex
                      const currentIndex = itemIndex
                      
                      return (
                        <button
                          key={cmd.id}
                          data-index={currentIndex}
                          onClick={() => { cmd.action(); onClose(); }}
                          onMouseEnter={() => setSelectedIndex(currentIndex)}
                          style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 12,
                            padding: '10px 20px',
                            background: isSelected ? 'var(--bg-tertiary)' : 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            textAlign: 'left',
                            transition: 'background 0.1s ease'
                          }}
                        >
                          <div style={{
                            width: 36,
                            height: 36,
                            borderRadius: 8,
                            background: isSelected ? 'var(--accent)' : 'var(--bg-tertiary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: isSelected ? 'white' : 'var(--text-muted)',
                            transition: 'all 0.1s ease'
                          }}>
                            {cmd.icon}
                          </div>
                          <div style={{ flex: 1 }}>
                            <div style={{
                              fontSize: 14,
                              fontWeight: 500,
                              color: 'var(--text-primary)'
                            }}>
                              {cmd.label}
                            </div>
                            {cmd.description && (
                              <div style={{
                                fontSize: 12,
                                color: 'var(--text-muted)',
                                marginTop: 1
                              }}>
                                {cmd.description}
                              </div>
                            )}
                          </div>
                          {isSelected && (
                            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
                          )}
                        </button>
                      )
                    })}
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div style={{
              padding: '12px 20px',
              borderTop: '1px solid var(--border-color)',
              background: 'var(--bg-tertiary)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              fontSize: 12,
              color: 'var(--text-muted)'
            }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <kbd style={{
                  padding: '2px 6px',
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 4,
                  fontSize: 10
                }}>↑↓</kbd>
                Navigate
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <kbd style={{
                  padding: '2px 6px',
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 4,
                  fontSize: 10
                }}>↵</kbd>
                Select
              </span>
              <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Command size={12} />
                Kahua Assistant
              </span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
})
