/**
 * AI Assistant Panel
 * 
 * Chat interface for AI-assisted template creation and refinement
 * Provides contextual help and quick actions based on current state
 */

import React, { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles, Send, X, Loader2, Lightbulb, RefreshCw, CheckCircle, Wand2,
  MessageSquare, ArrowRight, Zap, Layout, Table, FileText, List, Copy
} from 'lucide-react'
import { useBuilder } from './BuilderState'
import { PortableTemplate } from './types'

// ============== Quick Action Buttons ==============

interface QuickActionProps {
  label: string
  prompt: string
  icon: React.ElementType
  onClick: (prompt: string) => void
}

function QuickAction({ label, prompt, icon: Icon, onClick }: QuickActionProps) {
  return (
    <button
      className="quick-action-btn"
      onClick={() => onClick(prompt)}
    >
      <Icon size={14} />
      <span>{label}</span>
    </button>
  )
}

// ============== Message Component ==============

interface MessageProps {
  role: 'user' | 'assistant'
  content: string
}

function Message({ role, content }: MessageProps) {
  return (
    <div className={`ai-message ${role}`}>
      <div className="message-avatar">
        {role === 'assistant' ? <Sparkles size={16} /> : '👤'}
      </div>
      <div className="message-content">
        {content}
      </div>
    </div>
  )
}

// ============== Suggestion Card ==============

interface SuggestionCardProps {
  suggestion: string
  onApply: () => void
}

function SuggestionCard({ suggestion, onApply }: SuggestionCardProps) {
  return (
    <div className="suggestion-card">
      <div className="suggestion-icon">
        <Lightbulb size={14} />
      </div>
      <div className="suggestion-content">{suggestion}</div>
      <button className="apply-suggestion-btn" onClick={onApply}>
        <Wand2 size={12} />
        Apply
      </button>
    </div>
  )
}

// ============== Main AI Panel ==============

export function AIAssistant() {
  const { state, dispatch, actions } = useBuilder()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Context-aware quick actions
  const getContextualActions = () => {
    const hasEntity = !!state.template.target_entity_def
    const hasSections = state.template.sections.length > 0
    const hasHeader = state.template.sections.some(s => s.type === 'header')
    const hasTable = state.template.sections.some(s => s.type === 'table')
    const entityName = state.entitySchema?.display_name || 'record'
    
    if (!hasEntity) {
      return [
        { label: 'Create Contract template', prompt: 'Create a professional contract summary template with header, details, and line items', icon: FileText },
        { label: 'Create RFI template', prompt: 'Create an RFI document template with all standard fields', icon: FileText },
        { label: 'Create Submittal template', prompt: 'Create a submittal tracking template', icon: FileText },
      ]
    }
    
    if (!hasSections) {
      return [
        { label: `Build complete ${entityName} template`, prompt: `Create a complete ${entityName} report with header, key details, and any related items in a table`, icon: Layout },
        { label: 'Start with header', prompt: 'Add a professional header section with the main identifying information', icon: FileText },
        { label: 'Create simple layout', prompt: 'Create a simple single-page layout with just the essential fields', icon: List },
      ]
    }
    
    const actions = []
    if (!hasHeader) {
      actions.push({ label: 'Add header section', prompt: 'Add a header section with title and key identifying fields', icon: FileText })
    }
    if (!hasTable && (state.entitySchema?.child_entities?.length ?? 0) > 0) {
      actions.push({ label: 'Add items table', prompt: 'Add a table section to display the related items/line items', icon: Table })
    }
    actions.push({ label: 'Add more details', prompt: 'Add another detail section with additional fields', icon: List })
    actions.push({ label: 'Improve styling', prompt: 'Make the template look more professional with better formatting', icon: Sparkles })
    
    return actions.slice(0, 4)
  }

  const quickActions = getContextualActions()

  // Scroll to bottom when new messages appear
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.ai.conversation])

  // Focus input when panel opens
  useEffect(() => {
    if (state.ai.isOpen) {
      inputRef.current?.focus()
    }
  }, [state.ai.isOpen])

  const handleSend = useCallback(async () => {
    if (!input.trim() || state.ai.isLoading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message to conversation
    dispatch({ type: 'ADD_AI_MESSAGE', payload: { role: 'user', content: userMessage } })
    dispatch({ type: 'SET_AI_LOADING', payload: true })

    try {
      // Prepare request payload
      const payload = {
        instruction: userMessage,
        current_template: state.template,
        entity_schema: state.entitySchema,
      }
      
      console.log('[AI Assistant] Sending request:', payload)
      
      // Call AI endpoint
      const response = await fetch('/api/template/ai-assist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      console.log('[AI Assistant] Response status:', response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('[AI Assistant] Error response:', errorText)
        throw new Error(`AI request failed: ${response.status} - ${errorText}`)
      }

      const result = await response.json()
      console.log('[AI Assistant] Success result:', result)

      // Check for error status in response
      if (result.status === 'error') {
        dispatch({
          type: 'ADD_AI_MESSAGE',
          payload: { 
            role: 'assistant', 
            content: `I couldn't complete that request: ${result.message || 'Unknown error'}. Please try rephrasing or a simpler request.` 
          }
        })
        return
      }

      // Add assistant response
      dispatch({
        type: 'ADD_AI_MESSAGE',
        payload: { role: 'assistant', content: result.message || 'Template updated!' }
      })

      // Apply template changes if returned
      if (result.template) {
        dispatch({ type: 'APPLY_AI_TEMPLATE', payload: result.template })
      }

      // Update suggestions if returned
      if (result.suggestions) {
        dispatch({ type: 'SET_AI_SUGGESTIONS', payload: result.suggestions })
      }
    } catch (error: any) {
      console.error('[AI Assistant] Error:', error)
      dispatch({
        type: 'ADD_AI_MESSAGE',
        payload: { 
          role: 'assistant', 
          content: `Sorry, I encountered an error: ${error.message || 'Please try again.'}` 
        }
      })
    } finally {
      dispatch({ type: 'SET_AI_LOADING', payload: false })
    }
  }, [input, state.template, state.entitySchema, state.ai.isLoading, dispatch])

  const handleQuickAction = useCallback((prompt: string) => {
    setInput(prompt)
    // Optionally auto-send
    // handleSend()
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleClose = useCallback(() => {
    dispatch({ type: 'TOGGLE_AI', payload: false })
  }, [dispatch])

  if (!state.ai.isOpen) return null

  const entityName = state.entitySchema?.display_name || state.template.target_entity_def?.split('.').pop() || null
  const sectionCount = state.template.sections.length

  return (
    <motion.div
      className="ai-assistant-panel"
      initial={{ x: '100%', opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: '100%', opacity: 0 }}
      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
    >
      {/* Header */}
      <div className="ai-panel-header">
        <div className="ai-title">
          <Sparkles size={18} />
          <span>AI Assistant</span>
        </div>
        <button className="ai-close-btn" onClick={handleClose}>
          <X size={18} />
        </button>
      </div>

      {/* Context bar - shows current state */}
      <div className="ai-context-bar">
        <span className="context-item">
          {entityName ? `📋 ${entityName}` : '⚠️ No entity selected'}
        </span>
        <span className="context-dot">•</span>
        <span className="context-item">
          {sectionCount} section{sectionCount !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Quick actions - always visible when no conversation */}
      {state.ai.conversation.length === 0 && (
        <div className="ai-quick-actions">
          <p className="quick-actions-label">Quick actions</p>
          <div className="quick-actions-list">
            {quickActions.map((action, i) => (
              <QuickAction
                key={i}
                label={action.label}
                prompt={action.prompt}
                icon={action.icon}
                onClick={handleQuickAction}
              />
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="ai-messages">
        {state.ai.conversation.length === 0 ? (
          <div className="ai-empty-state">
            <div className="ai-empty-icon">
              <Sparkles size={28} />
            </div>
            <h4>How can I help?</h4>
            <p>Describe your template in plain language, or use a quick action above.</p>
            <div className="ai-examples">
              <p className="examples-label">Example prompts:</p>
              <ul>
                <li onClick={() => setInput('Create a professional contract summary')}>
                  "Create a professional contract summary"
                </li>
                <li onClick={() => setInput('Add a table showing all line items with amounts')}>
                  "Add a table showing all line items"
                </li>
                <li onClick={() => setInput('Make this template more compact')}>
                  "Make this template more compact"
                </li>
              </ul>
            </div>
          </div>
        ) : (
          <>
            {state.ai.conversation.map((msg, i) => (
              <Message key={i} role={msg.role} content={msg.content} />
            ))}
          </>
        )}

        {state.ai.isLoading && (
          <div className="ai-loading">
            <Loader2 size={16} className="spin" />
            <span>Thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {state.ai.suggestions.length > 0 && (
        <div className="ai-suggestions">
          <p className="suggestions-label">Suggestions:</p>
          {state.ai.suggestions.map((suggestion, i) => (
            <SuggestionCard
              key={i}
              suggestion={suggestion}
              onApply={() => {
                setInput(suggestion)
              }}
            />
          ))}
        </div>
      )}

      {/* Input */}
      <div className="ai-input-container">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want to create or change..."
          rows={2}
          disabled={state.ai.isLoading}
        />
        <button
          className="ai-send-btn"
          onClick={handleSend}
          disabled={!input.trim() || state.ai.isLoading}
        >
          {state.ai.isLoading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
        </button>
      </div>
    </motion.div>
  )
}

// ============== AI Toggle Button ==============

export function AIToggleButton() {
  const { state, dispatch } = useBuilder()

  return (
    <button
      className={`ai-toggle-btn ${state.ai.isOpen ? 'active' : ''}`}
      onClick={() => dispatch({ type: 'TOGGLE_AI' })}
      title="AI Assistant"
    >
      <Sparkles size={18} />
      <span>AI Assist</span>
    </button>
  )
}

export default AIAssistant
