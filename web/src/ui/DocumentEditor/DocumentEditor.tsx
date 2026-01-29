/**
 * Document Editor - Template Designer
 * 
 * A document-first template editor with inline AI assistance.
 * Inspired by VS Code/Cursor inline editing and Notion's slash commands.
 */

import React, {
  useState, useCallback, useEffect, useRef, useMemo,
  KeyboardEvent, ClipboardEvent, FormEvent
} from 'react'
import {
  FileText, Save, Eye, Code, Download, Undo2, Redo2,
  Sparkles, X, Check, Loader2, ChevronDown, Settings,
  Image, BarChart2, Table, Type, List, Hash
} from 'lucide-react'
import './DocumentEditor.css'

// ============== Types ==============

interface EntityField {
  path: string
  label: string
  type: string
  format?: string
}

interface EntitySchema {
  entity_def: string
  display_name: string
  attributes: EntityField[]
  child_entities?: { path: string; display_name: string; attributes: EntityField[] }[]
}

interface DocumentState {
  content: string
  name: string
  entityDef: string
  isDirty: boolean
  history: string[]
  historyIndex: number
}

interface InlineCompletion {
  type: 'field' | 'filter' | 'command' | 'ai'
  trigger: string
  items: CompletionItem[]
  position: { top: number; left: number }
  selectedIndex: number
}

interface CompletionItem {
  label: string
  detail?: string
  insertText: string
  icon?: React.ReactNode
  category?: string
}

interface AIInlineState {
  active: boolean
  position: { top: number; left: number; width: number }
  prompt: string
  isStreaming: boolean
  streamedText: string
  selectionStart: number
  selectionEnd: number
}

// Selection toolbar state
interface SelectionToolbarState {
  visible: boolean
  position: { top: number; left: number }
  selectedText: string
  selectionStart: number
  selectionEnd: number
}

// Quick AI actions for selection toolbar
const QUICK_ACTIONS = [
  { id: 'formal', label: 'More formal', icon: '📝', prompt: 'Rewrite this text in a more formal, professional tone' },
  { id: 'casual', label: 'More casual', icon: '💬', prompt: 'Rewrite this text in a more casual, friendly tone' },
  { id: 'shorter', label: 'Make shorter', icon: '✂️', prompt: 'Make this text more concise while keeping the meaning' },
  { id: 'longer', label: 'Expand', icon: '📖', prompt: 'Expand this text with more detail and context' },
  { id: 'fix', label: 'Fix grammar', icon: '✓', prompt: 'Fix any grammar, spelling, or punctuation errors in this text' },
  { id: 'table', label: 'To table', icon: '▦', prompt: 'Convert this content into a markdown table format' },
  { id: 'bullets', label: 'To bullets', icon: '•', prompt: 'Convert this content into a bulleted list' },
] as const

// ============== Constants ==============

const JINJA_FILTERS = [
  { label: 'default', detail: 'Fallback value if empty', insertText: "default('-')" },
  { label: 'currency', detail: 'Format as currency', insertText: 'currency' },
  { label: 'date', detail: 'Format as date', insertText: 'date' },
  { label: 'datetime', detail: 'Format as datetime', insertText: 'datetime' },
  { label: 'upper', detail: 'Uppercase text', insertText: 'upper' },
  { label: 'lower', detail: 'Lowercase text', insertText: 'lower' },
  { label: 'title', detail: 'Title case', insertText: 'title' },
  { label: 'round', detail: 'Round number', insertText: 'round(2)' },
]

const SLASH_COMMANDS: CompletionItem[] = [
  { label: 'AI Help', detail: 'Ask AI to write or edit', insertText: '', icon: <Sparkles size={14} />, category: 'ai' },
  { label: 'Field', detail: 'Insert entity field', insertText: '{{ ', icon: <Hash size={14} />, category: 'insert' },
  { label: 'Table', detail: 'Insert data table', insertText: '| Column 1 | Column 2 |\n|----------|----------|\n| {{ field }} | {{ field }} |', icon: <Table size={14} />, category: 'insert' },
  { label: 'Heading 1', detail: 'Large heading', insertText: '# ', icon: <Type size={14} />, category: 'format' },
  { label: 'Heading 2', detail: 'Medium heading', insertText: '## ', icon: <Type size={14} />, category: 'format' },
  { label: 'Heading 3', detail: 'Small heading', insertText: '### ', icon: <Type size={14} />, category: 'format' },
  { label: 'Bullet List', detail: 'Bulleted list', insertText: '- ', icon: <List size={14} />, category: 'format' },
  { label: 'For Loop', detail: 'Iterate over items', insertText: '{% for item in Items %}\n  {{ item.field }}\n{% endfor %}', icon: <Code size={14} />, category: 'logic' },
  { label: 'If Condition', detail: 'Conditional content', insertText: '{% if field %}\n  content\n{% endif %}', icon: <Code size={14} />, category: 'logic' },
  { label: 'Image', detail: 'Insert image placeholder', insertText: '![Description](image_url)', icon: <Image size={14} />, category: 'media' },
  { label: 'Horizontal Rule', detail: 'Divider line', insertText: '\n---\n', icon: <FileText size={14} />, category: 'format' },
]

const DEFAULT_CONTENT = `# {{ Number }} - {{ Subject | default }}

---

| | |
|:--|:--|
| **Status** | {{ Status.Name | default }} |
| **Priority** | {{ Priority.Name | default }} |
| **Date** | {{ DateSubmitted | date }} |

## Details

{{ Description | default('No description provided.') }}

---

*Generated {{ _today }}*
`

// ============== Entity Schema Loader ==============

const ENTITY_SCHEMAS: Record<string, EntitySchema> = {
  'kahua_AEC_RFI.RFI': {
    entity_def: 'kahua_AEC_RFI.RFI',
    display_name: 'RFI',
    attributes: [
      { path: 'Number', label: 'RFI Number', type: 'string', format: 'text' },
      { path: 'Subject', label: 'Subject', type: 'string', format: 'text' },
      { path: 'Description', label: 'Description', type: 'string', format: 'rich_text' },
      { path: 'Status.Name', label: 'Status', type: 'string', format: 'text' },
      { path: 'Priority.Name', label: 'Priority', type: 'string', format: 'text' },
      { path: 'DateSubmitted', label: 'Date Submitted', type: 'string', format: 'date' },
      { path: 'DateRequired', label: 'Date Required', type: 'string', format: 'date' },
      { path: 'DateClosed', label: 'Date Closed', type: 'string', format: 'date' },
      { path: 'Question', label: 'Question', type: 'string', format: 'rich_text' },
      { path: 'Answer', label: 'Answer', type: 'string', format: 'rich_text' },
      { path: 'SubmittedBy.Name', label: 'Submitted By', type: 'string', format: 'text' },
      { path: 'AssignedTo.Name', label: 'Assigned To', type: 'string', format: 'text' },
      { path: 'CostImpact', label: 'Cost Impact', type: 'number', format: 'currency' },
      { path: 'ScheduleImpact', label: 'Schedule Impact', type: 'number', format: 'number' },
    ]
  },
  'kahua_Contract.Contract': {
    entity_def: 'kahua_Contract.Contract',
    display_name: 'Contract',
    attributes: [
      { path: 'Number', label: 'Contract Number', type: 'string', format: 'text' },
      { path: 'Name', label: 'Contract Name', type: 'string', format: 'text' },
      { path: 'Description', label: 'Description', type: 'string', format: 'rich_text' },
      { path: 'Status.Name', label: 'Status', type: 'string', format: 'text' },
      { path: 'OriginalAmount', label: 'Original Amount', type: 'number', format: 'currency' },
      { path: 'ApprovedChanges', label: 'Approved Changes', type: 'number', format: 'currency' },
      { path: 'RevisedAmount', label: 'Revised Amount', type: 'number', format: 'currency' },
      { path: 'StartDate', label: 'Start Date', type: 'string', format: 'date' },
      { path: 'EndDate', label: 'End Date', type: 'string', format: 'date' },
      { path: 'Vendor.Name', label: 'Vendor', type: 'string', format: 'text' },
    ],
    child_entities: [
      {
        path: 'Items',
        display_name: 'Contract Items',
        attributes: [
          { path: 'Number', label: 'Item Number', type: 'string' },
          { path: 'Description', label: 'Description', type: 'string' },
          { path: 'Amount', label: 'Amount', type: 'number', format: 'currency' },
        ]
      }
    ]
  },
  'kahua_AEC_PunchList.PunchListItem': {
    entity_def: 'kahua_AEC_PunchList.PunchListItem',
    display_name: 'Punch List Item',
    attributes: [
      { path: 'Number', label: 'Item Number', type: 'string' },
      { path: 'Description', label: 'Description', type: 'string' },
      { path: 'Status.Name', label: 'Status', type: 'string' },
      { path: 'Priority.Name', label: 'Priority', type: 'string' },
      { path: 'Location', label: 'Location', type: 'string' },
      { path: 'AssignedTo.Name', label: 'Assigned To', type: 'string' },
      { path: 'DateDue', label: 'Date Due', type: 'string', format: 'date' },
    ]
  },
  'kahua_AEC_Submittal.Submittal': {
    entity_def: 'kahua_AEC_Submittal.Submittal',
    display_name: 'Submittal',
    attributes: [
      { path: 'Number', label: 'Submittal Number', type: 'string' },
      { path: 'Subject', label: 'Subject', type: 'string' },
      { path: 'Description', label: 'Description', type: 'string', format: 'rich_text' },
      { path: 'Status.Name', label: 'Status', type: 'string' },
      { path: 'SubmittalType.Name', label: 'Type', type: 'string' },
      { path: 'SpecSection', label: 'Spec Section', type: 'string' },
      { path: 'DateSubmitted', label: 'Date Submitted', type: 'string', format: 'date' },
      { path: 'DateRequired', label: 'Date Required', type: 'string', format: 'date' },
      { path: 'DateReturned', label: 'Date Returned', type: 'string', format: 'date' },
      { path: 'SubmittedBy.Name', label: 'Submitted By', type: 'string' },
      { path: 'AssignedTo.Name', label: 'Assigned To', type: 'string' },
    ]
  },
  'kahua_AEC_ChangeOrder.ChangeOrder': {
    entity_def: 'kahua_AEC_ChangeOrder.ChangeOrder',
    display_name: 'Change Order',
    attributes: [
      { path: 'Number', label: 'CO Number', type: 'string' },
      { path: 'Subject', label: 'Subject', type: 'string' },
      { path: 'Description', label: 'Description', type: 'string', format: 'rich_text' },
      { path: 'Status.Name', label: 'Status', type: 'string' },
      { path: 'Amount', label: 'Amount', type: 'number', format: 'currency' },
      { path: 'ScheduleImpact', label: 'Schedule Impact (days)', type: 'number' },
      { path: 'DateSubmitted', label: 'Date Submitted', type: 'string', format: 'date' },
      { path: 'DateApproved', label: 'Date Approved', type: 'string', format: 'date' },
      { path: 'SubmittedBy.Name', label: 'Submitted By', type: 'string' },
      { path: 'Reason.Name', label: 'Reason', type: 'string' },
    ]
  },
  'kahua_AEC_DailyLog.DailyLog': {
    entity_def: 'kahua_AEC_DailyLog.DailyLog',
    display_name: 'Daily Log',
    attributes: [
      { path: 'Number', label: 'Log Number', type: 'string' },
      { path: 'Date', label: 'Date', type: 'string', format: 'date' },
      { path: 'Weather', label: 'Weather', type: 'string' },
      { path: 'Temperature', label: 'Temperature', type: 'string' },
      { path: 'WorkPerformed', label: 'Work Performed', type: 'string', format: 'rich_text' },
      { path: 'Notes', label: 'Notes', type: 'string', format: 'rich_text' },
      { path: 'CreatedBy.Name', label: 'Created By', type: 'string' },
    ]
  }
}

// ============== Hooks ==============

function useHistory(initialContent: string) {
  const [history, setHistory] = useState<string[]>([initialContent])
  const [index, setIndex] = useState(0)
  
  const push = useCallback((content: string) => {
    setHistory(prev => {
      const newHistory = prev.slice(0, index + 1)
      newHistory.push(content)
      // Limit history size
      if (newHistory.length > 100) newHistory.shift()
      return newHistory
    })
    setIndex(prev => Math.min(prev + 1, 99))
  }, [index])
  
  const undo = useCallback(() => {
    if (index > 0) {
      setIndex(prev => prev - 1)
      return history[index - 1]
    }
    return null
  }, [index, history])
  
  const redo = useCallback(() => {
    if (index < history.length - 1) {
      setIndex(prev => prev + 1)
      return history[index + 1]
    }
    return null
  }, [index, history])
  
  return { push, undo, redo, canUndo: index > 0, canRedo: index < history.length - 1 }
}

// ============== Inline Completion Component ==============

interface CompletionMenuProps {
  completion: InlineCompletion
  onSelect: (item: CompletionItem) => void
  onClose: () => void
}

function CompletionMenu({ completion, onSelect, onClose }: CompletionMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])
  
  // Group by category for slash commands
  const grouped = useMemo(() => {
    if (completion.type !== 'command') return null
    const groups: Record<string, CompletionItem[]> = {}
    completion.items.forEach(item => {
      const cat = item.category || 'other'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(item)
    })
    return groups
  }, [completion])
  
  return (
    <div
      ref={menuRef}
      className="completion-menu"
      style={{ top: completion.position.top, left: completion.position.left }}
    >
      {completion.type === 'command' && grouped ? (
        Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="completion-group">
            <div className="completion-group-label">{category}</div>
            {items.map((item, i) => {
              const globalIndex = completion.items.indexOf(item)
              return (
                <div
                  key={item.label}
                  className={`completion-item ${globalIndex === completion.selectedIndex ? 'selected' : ''}`}
                  onClick={() => onSelect(item)}
                >
                  {item.icon && <span className="completion-icon">{item.icon}</span>}
                  <span className="completion-label">{item.label}</span>
                  {item.detail && <span className="completion-detail">{item.detail}</span>}
                </div>
              )
            })}
          </div>
        ))
      ) : (
        completion.items.map((item, i) => (
          <div
            key={item.label}
            className={`completion-item ${i === completion.selectedIndex ? 'selected' : ''}`}
            onClick={() => onSelect(item)}
          >
            {item.icon && <span className="completion-icon">{item.icon}</span>}
            <span className="completion-label">{item.label}</span>
            {item.detail && <span className="completion-detail">{item.detail}</span>}
          </div>
        ))
      )}
    </div>
  )
}

// ============== AI Inline Editor ==============

interface AIInlineEditorProps {
  state: AIInlineState
  onSubmit: (prompt: string) => void
  onCancel: () => void
  onAccept: () => void
  onPromptChange: (prompt: string) => void
}

function AIInlineEditor({ state, onSubmit, onCancel, onAccept, onPromptChange }: AIInlineEditorProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  
  useEffect(() => {
    if (state.active && inputRef.current) {
      inputRef.current.focus()
    }
  }, [state.active])
  
  if (!state.active) return null
  
  return (
    <div
      className="ai-inline-editor"
      style={{ top: state.position.top, left: state.position.left, width: state.position.width }}
    >
      <div className="ai-inline-header">
        <Sparkles size={14} className="ai-icon" />
        <span>AI Edit</span>
        {state.isStreaming && <Loader2 size={14} className="spinning" />}
      </div>
      
      {!state.isStreaming && !state.streamedText && (
        <form onSubmit={(e) => { e.preventDefault(); onSubmit(state.prompt) }}>
          <input
            ref={inputRef}
            type="text"
            value={state.prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            placeholder="Describe what you want..."
            className="ai-inline-input"
          />
          <div className="ai-inline-hint">
            Press <kbd>Enter</kbd> to generate, <kbd>Esc</kbd> to cancel
          </div>
        </form>
      )}
      
      {(state.isStreaming || state.streamedText) && (
        <div className="ai-inline-preview">
          <pre>{state.streamedText || '...'}</pre>
          {!state.isStreaming && (
            <div className="ai-inline-actions">
              <button className="ai-accept" onClick={onAccept}>
                <Check size={14} /> Accept
              </button>
              <button className="ai-reject" onClick={onCancel}>
                <X size={14} /> Reject
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============== Selection Toolbar (Canvas-style) ==============

interface SelectionToolbarProps {
  state: SelectionToolbarState
  onQuickAction: (actionId: string, prompt: string) => void
  onCustomPrompt: () => void
  onClose: () => void
}

function SelectionToolbar({ state, onQuickAction, onCustomPrompt, onClose }: SelectionToolbarProps) {
  const toolbarRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (toolbarRef.current && !toolbarRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    if (state.visible) {
      // Delay to avoid immediate close from selection event
      setTimeout(() => document.addEventListener('mousedown', handleClickOutside), 100)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [state.visible, onClose])
  
  if (!state.visible) return null
  
  return (
    <div
      ref={toolbarRef}
      className="selection-toolbar"
      style={{ top: state.position.top, left: state.position.left }}
    >
      <div className="selection-toolbar-actions">
        {QUICK_ACTIONS.map(action => (
          <button
            key={action.id}
            className="quick-action-btn"
            onClick={() => onQuickAction(action.id, action.prompt)}
            title={action.label}
          >
            <span className="quick-action-icon">{action.icon}</span>
            <span className="quick-action-label">{action.label}</span>
          </button>
        ))}
      </div>
      <div className="selection-toolbar-divider" />
      <button className="custom-prompt-btn" onClick={onCustomPrompt}>
        <Sparkles size={14} />
        Custom edit...
      </button>
    </div>
  )
}

// ============== Preview Panel ==============

interface PreviewPanelProps {
  content: string
  sampleData: Record<string, any>
}

function PreviewPanel({ content, sampleData }: PreviewPanelProps) {
  const rendered = useMemo(() => {
    // Simple Jinja2-like rendering for preview
    let result = content
    
    // Replace {{ field }} patterns
    result = result.replace(/\{\{\s*([^}|]+?)(?:\s*\|\s*([^}]+))?\s*\}\}/g, (match, field, filter) => {
      const path = field.trim()
      let value = getNestedValue(sampleData, path)
      
      if (value === undefined || value === null) {
        // Check for default filter
        if (filter?.includes('default')) {
          const defaultMatch = filter.match(/default\(['"]?([^'")\s]+)['"]?\)/)
          return defaultMatch ? defaultMatch[1] : '-'
        }
        return '-'
      }
      
      // Apply filters
      if (filter) {
        if (filter.includes('currency')) {
          value = typeof value === 'number' ? `$${value.toLocaleString()}` : value
        } else if (filter.includes('date')) {
          value = formatDate(value)
        } else if (filter.includes('upper')) {
          value = String(value).toUpperCase()
        }
      }
      
      return String(value)
    })
    
    // Replace {{ _today }}
    result = result.replace(/\{\{\s*_today\s*\}\}/g, new Date().toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric'
    }))
    
    return result
  }, [content, sampleData])
  
  return (
    <div className="preview-panel">
      <div className="preview-header">
        <Eye size={14} />
        <span>Live Preview</span>
      </div>
      <div className="preview-content markdown-body">
        <div dangerouslySetInnerHTML={{ __html: markdownToHtml(rendered) }} />
      </div>
    </div>
  )
}

function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((curr, key) => curr?.[key], obj)
}

function formatDate(value: any): string {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return String(value)
  }
}

function markdownToHtml(md: string): string {
  // Simple markdown conversion
  let html = md
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // HR
    .replace(/^---$/gm, '<hr />')
    // Tables (basic)
    .replace(/^\|(.+)\|$/gm, (match, content) => {
      if (content.includes('---')) return ''
      const cells = content.split('|').map((c: string) => c.trim())
      return '<tr>' + cells.map((c: string) => `<td>${c}</td>`).join('') + '</tr>'
    })
    // Wrap tables
    .replace(/(<tr>[\s\S]*?<\/tr>)+/g, '<table>$&</table>')
    // Paragraphs
    .replace(/\n\n/g, '</p><p>')
  
  return `<p>${html}</p>`
}

// ============== Main Document Editor ==============

interface DocumentEditorProps {
  templateId?: string
  entityDef?: string
  initialContent?: string
  onSave?: (content: string, name: string) => void
  onClose?: () => void
}

export function DocumentEditor({
  templateId,
  entityDef = 'kahua_AEC_RFI.RFI',
  initialContent,
  onSave,
  onClose
}: DocumentEditorProps) {
  const editorRef = useRef<HTMLTextAreaElement>(null)
  const [content, setContent] = useState(initialContent || DEFAULT_CONTENT)
  const [name, setName] = useState('Untitled Template')
  const [selectedEntity, setSelectedEntity] = useState(entityDef)
  const [showPreview, setShowPreview] = useState(true)
  const [showCode, setShowCode] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  
  // Completion state
  const [completion, setCompletion] = useState<InlineCompletion | null>(null)
  
  // AI inline state
  const [aiState, setAiState] = useState<AIInlineState>({
    active: false,
    position: { top: 0, left: 0, width: 400 },
    prompt: '',
    isStreaming: false,
    streamedText: '',
    selectionStart: 0,
    selectionEnd: 0
  })
  
  // Selection toolbar state (Canvas-style)
  const [selectionToolbar, setSelectionToolbar] = useState<SelectionToolbarState>({
    visible: false,
    position: { top: 0, left: 0 },
    selectedText: '',
    selectionStart: 0,
    selectionEnd: 0
  })
  
  // History
  const { push: pushHistory, undo, redo, canUndo, canRedo } = useHistory(content)
  
  // Schema
  const schema = ENTITY_SCHEMAS[selectedEntity]
  
  // Sample data for preview
  const sampleData = useMemo(() => ({
    Number: 'RFI-0042',
    Subject: 'Structural Steel Connection Detail',
    Description: 'Need clarification on the connection detail for the moment frame at grid line B-4.',
    'Status': { Name: 'Open' },
    'Priority': { Name: 'High' },
    DateSubmitted: '2026-01-15',
    DateRequired: '2026-01-22',
    Question: 'Please confirm the bolt size and grade for the connection.',
    SubmittedBy: { Name: 'John Smith' },
    AssignedTo: { Name: 'Jane Doe' },
    CostImpact: 5000,
    ScheduleImpact: 3,
    _today: new Date().toLocaleDateString()
  }), [])
  
  // ============== Completion Logic ==============
  
  const getCaretCoordinates = useCallback(() => {
    const textarea = editorRef.current
    if (!textarea) return { top: 0, left: 0 }
    
    // Create mirror div to calculate position
    const mirror = document.createElement('div')
    const style = window.getComputedStyle(textarea)
    
    mirror.style.cssText = `
      position: absolute;
      visibility: hidden;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-family: ${style.fontFamily};
      font-size: ${style.fontSize};
      line-height: ${style.lineHeight};
      padding: ${style.padding};
      width: ${textarea.clientWidth}px;
    `
    
    const textBefore = textarea.value.substring(0, textarea.selectionStart)
    mirror.textContent = textBefore
    
    const marker = document.createElement('span')
    marker.textContent = '|'
    mirror.appendChild(marker)
    
    document.body.appendChild(mirror)
    
    const rect = textarea.getBoundingClientRect()
    const markerRect = marker.getBoundingClientRect()
    
    document.body.removeChild(mirror)
    
    return {
      top: rect.top + (markerRect.top - mirror.getBoundingClientRect().top) + 24,
      left: rect.left + (markerRect.left - mirror.getBoundingClientRect().left)
    }
  }, [])
  
  const checkForTrigger = useCallback((value: string, position: number) => {
    const textBefore = value.substring(0, position)
    
    // Check for {{ trigger (field autocomplete)
    const fieldMatch = textBefore.match(/\{\{\s*(\w*)$/)
    if (fieldMatch) {
      const query = fieldMatch[1].toLowerCase()
      const items: CompletionItem[] = (schema?.attributes || [])
        .filter(attr => attr.path.toLowerCase().includes(query) || attr.label.toLowerCase().includes(query))
        .map(attr => ({
          label: attr.path,
          detail: attr.label,
          insertText: attr.path + ' ',
          icon: <Hash size={14} />
        }))
      
      if (items.length > 0) {
        setCompletion({
          type: 'field',
          trigger: fieldMatch[0],
          items,
          position: getCaretCoordinates(),
          selectedIndex: 0
        })
        return
      }
    }
    
    // Check for | trigger (filter autocomplete)
    const filterMatch = textBefore.match(/\{\{[^}]+\|\s*(\w*)$/)
    if (filterMatch) {
      const query = filterMatch[1].toLowerCase()
      const items = JINJA_FILTERS
        .filter(f => f.label.toLowerCase().includes(query))
        .map(f => ({
          label: f.label,
          detail: f.detail,
          insertText: f.insertText + ' }}',
          icon: <Code size={14} />
        }))
      
      if (items.length > 0) {
        setCompletion({
          type: 'filter',
          trigger: filterMatch[0],
          items,
          position: getCaretCoordinates(),
          selectedIndex: 0
        })
        return
      }
    }
    
    // Check for / trigger (slash commands) - works anywhere
    const slashMatch = textBefore.match(/\/(\w*)$/)
    if (slashMatch) {
      const query = slashMatch[1].toLowerCase()
      const items = SLASH_COMMANDS.filter(c => 
        c.label.toLowerCase().includes(query)
      )
      
      if (items.length > 0) {
        setCompletion({
          type: 'command',
          trigger: slashMatch[0],
          items,
          position: getCaretCoordinates(),
          selectedIndex: 0
        })
        return
      }
    }
    
    setCompletion(null)
  }, [schema, getCaretCoordinates])
  
  const handleCompletionSelect = useCallback((item: CompletionItem) => {
    if (!completion || !editorRef.current) return
    
    const textarea = editorRef.current
    const pos = textarea.selectionStart
    
    // Special case: AI Help
    if (item.category === 'ai') {
      const coords = getCaretCoordinates()
      setAiState({
        active: true,
        position: { top: coords.top, left: coords.left, width: Math.min(400, window.innerWidth - coords.left - 20) },
        prompt: '',
        isStreaming: false,
        streamedText: '',
        selectionStart: pos - completion.trigger.length,
        selectionEnd: pos
      })
      setCompletion(null)
      return
    }
    
    // Insert the completion
    const before = content.substring(0, pos - completion.trigger.length + (completion.type === 'field' ? 3 : 0))
    const after = content.substring(pos)
    
    let insertText = item.insertText
    if (completion.type === 'field') {
      insertText = item.insertText
    } else if (completion.type === 'command') {
      // Remove the / trigger
      insertText = item.insertText
    }
    
    const newContent = before + insertText + after
    setContent(newContent)
    pushHistory(newContent)
    
    // Set cursor position
    setTimeout(() => {
      if (editorRef.current) {
        const newPos = before.length + insertText.length
        editorRef.current.selectionStart = newPos
        editorRef.current.selectionEnd = newPos
        editorRef.current.focus()
      }
    }, 0)
    
    setCompletion(null)
  }, [completion, content, pushHistory, getCaretCoordinates])
  
  // ============== AI Inline Logic ==============
  
  const handleAISubmit = useCallback(async (prompt: string) => {
    setAiState(prev => ({ ...prev, isStreaming: true, streamedText: '' }))
    
    try {
      const response = await fetch('/api/template/ai-inline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          context: content,
          entityDef: selectedEntity,
          selectionStart: aiState.selectionStart,
          selectionEnd: aiState.selectionEnd
        })
      })
      
      if (!response.ok) throw new Error('AI request failed')
      
      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')
      
      const decoder = new TextDecoder()
      let fullText = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            try {
              const parsed = JSON.parse(data)
              if (parsed.text) {
                fullText += parsed.text
                setAiState(prev => ({ ...prev, streamedText: fullText }))
              }
            } catch {}
          }
        }
      }
      
      setAiState(prev => ({ ...prev, isStreaming: false }))
    } catch (error) {
      console.error('AI error:', error)
      setAiState(prev => ({ ...prev, isStreaming: false, streamedText: '// Error generating content' }))
    }
  }, [content, selectedEntity, aiState.selectionStart, aiState.selectionEnd])
  
  const handleAIAccept = useCallback(() => {
    if (!aiState.streamedText) return
    
    const before = content.substring(0, aiState.selectionStart)
    const after = content.substring(aiState.selectionEnd)
    const newContent = before + aiState.streamedText + after
    
    setContent(newContent)
    pushHistory(newContent)
    setAiState(prev => ({ ...prev, active: false, streamedText: '', prompt: '' }))
  }, [content, aiState, pushHistory])
  
  const handleAICancel = useCallback(() => {
    setAiState(prev => ({ ...prev, active: false, streamedText: '', prompt: '' }))
  }, [])
  
  // ============== Selection Toolbar (Canvas-style) ==============
  
  const handleSelectionChange = useCallback(() => {
    const textarea = editorRef.current
    if (!textarea) return
    
    const { selectionStart, selectionEnd } = textarea
    const selectedText = textarea.value.substring(selectionStart, selectionEnd).trim()
    
    // Only show toolbar if there's a meaningful selection (not just cursor)
    if (selectedText.length > 2) {
      const coords = getCaretCoordinates()
      setSelectionToolbar({
        visible: true,
        position: { top: coords.top - 50, left: coords.left },
        selectedText,
        selectionStart,
        selectionEnd
      })
    } else {
      setSelectionToolbar(prev => ({ ...prev, visible: false }))
    }
  }, [getCaretCoordinates])
  
  const handleQuickAction = useCallback(async (actionId: string, prompt: string) => {
    const { selectedText, selectionStart, selectionEnd } = selectionToolbar
    if (!selectedText) return
    
    // Hide toolbar, show AI inline editor with the prompt pre-filled
    setSelectionToolbar(prev => ({ ...prev, visible: false }))
    
    // Set up AI state and immediately submit
    setAiState({
      active: true,
      position: { top: selectionToolbar.position.top + 50, left: selectionToolbar.position.left, width: 400 },
      prompt: `${prompt}: "${selectedText}"`,
      isStreaming: true,
      streamedText: '',
      selectionStart,
      selectionEnd
    })
    
    // Auto-submit the quick action
    try {
      const response = await fetch('/api/template/ai-inline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: `${prompt}. Here is the text to transform:\n\n${selectedText}\n\nRespond with ONLY the transformed text, no explanations.`,
          context: content,
          entityDef: selectedEntity,
          selectionStart,
          selectionEnd
        })
      })
      
      if (!response.ok) throw new Error('AI request failed')
      
      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')
      
      const decoder = new TextDecoder()
      let fullText = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            try {
              const parsed = JSON.parse(data)
              if (parsed.text) {
                fullText += parsed.text
                setAiState(prev => ({ ...prev, streamedText: fullText }))
              }
            } catch {}
          }
        }
      }
      
      setAiState(prev => ({ ...prev, isStreaming: false }))
    } catch (error) {
      console.error('Quick action error:', error)
      setAiState(prev => ({ ...prev, isStreaming: false, streamedText: '// Error - try again' }))
    }
  }, [selectionToolbar, content, selectedEntity])
  
  const handleCustomPromptFromToolbar = useCallback(() => {
    const { selectionStart, selectionEnd } = selectionToolbar
    setSelectionToolbar(prev => ({ ...prev, visible: false }))
    
    const coords = getCaretCoordinates()
    setAiState({
      active: true,
      position: { top: coords.top, left: coords.left, width: 400 },
      prompt: '',
      isStreaming: false,
      streamedText: '',
      selectionStart,
      selectionEnd
    })
  }, [selectionToolbar, getCaretCoordinates])
  
  // ============== Keyboard Handling ==============
  
  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Handle completion navigation
    if (completion) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setCompletion(prev => prev ? {
          ...prev,
          selectedIndex: Math.min(prev.selectedIndex + 1, prev.items.length - 1)
        } : null)
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setCompletion(prev => prev ? {
          ...prev,
          selectedIndex: Math.max(prev.selectedIndex - 1, 0)
        } : null)
        return
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault()
        handleCompletionSelect(completion.items[completion.selectedIndex])
        return
      }
      if (e.key === 'Escape') {
        e.preventDefault()
        setCompletion(null)
        return
      }
    }
    
    // Ctrl+I for AI inline edit (not Ctrl+K which conflicts with browser)
    if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
      e.preventDefault()
      const textarea = editorRef.current
      if (!textarea) return
      
      const coords = getCaretCoordinates()
      setAiState({
        active: true,
        position: { top: coords.top, left: coords.left, width: Math.min(400, window.innerWidth - coords.left - 20) },
        prompt: '',
        isStreaming: false,
        streamedText: '',
        selectionStart: textarea.selectionStart,
        selectionEnd: textarea.selectionEnd
      })
      return
    }
    
    // Ctrl+Z for undo
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
      e.preventDefault()
      const prev = undo()
      if (prev !== null) setContent(prev)
      return
    }
    
    // Ctrl+Shift+Z or Ctrl+Y for redo
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
      e.preventDefault()
      const next = redo()
      if (next !== null) setContent(next)
      return
    }
    
    // Ctrl+S for save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      handleSave()
      return
    }
  }, [completion, handleCompletionSelect, undo, redo, getCaretCoordinates])
  
  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    setContent(newValue)
    checkForTrigger(newValue, e.target.selectionStart)
  }, [checkForTrigger])
  
  const handleSave = useCallback(async () => {
    setIsSaving(true)
    try {
      const response = await fetch('/api/template/save-markdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          entityDef: selectedEntity,
          markdown: content
        })
      })
      
      if (!response.ok) throw new Error('Save failed')
      
      const result = await response.json()
      pushHistory(content)
      onSave?.(content, name)
    } catch (error) {
      console.error('Save error:', error)
    } finally {
      setIsSaving(false)
    }
  }, [content, name, selectedEntity, onSave, pushHistory])
  
  // ============== Render ==============
  
  return (
    <div className="document-editor">
      {/* Header */}
      <header className="editor-header">
        <div className="header-left">
          {onClose && (
            <button className="icon-btn" onClick={onClose} title="Close">
              <X size={18} />
            </button>
          )}
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="template-name-input"
            placeholder="Template name..."
          />
        </div>
        
        <div className="header-right">
          <button
            className={`icon-btn ${showPreview ? 'active' : ''}`}
            onClick={() => setShowPreview(!showPreview)}
            title="Toggle Preview"
          >
            <Eye size={18} />
          </button>
          <button
            className="icon-btn"
            onClick={() => { const prev = undo(); if (prev) setContent(prev) }}
            disabled={!canUndo}
            title="Undo (Ctrl+Z)"
          >
            <Undo2 size={18} />
          </button>
          <button
            className="icon-btn"
            onClick={() => { const next = redo(); if (next) setContent(next) }}
            disabled={!canRedo}
            title="Redo (Ctrl+Y)"
          >
            <Redo2 size={18} />
          </button>
          <button
            className="save-btn"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? <Loader2 size={16} className="spinning" /> : <Save size={16} />}
            Save
          </button>
        </div>
      </header>
      
      {/* Entity Type Selector Pills */}
      <div className="entity-selector">
        <span className="entity-selector-label">Entity:</span>
        <div className="entity-pills">
          {Object.entries(ENTITY_SCHEMAS).map(([def, schema]) => (
            <button
              key={def}
              className={`entity-pill ${selectedEntity === def ? 'active' : ''}`}
              onClick={() => setSelectedEntity(def)}
            >
              {schema.display_name}
            </button>
          ))}
        </div>
      </div>
      
      {/* Main Content */}
      <div className="editor-main">
        {/* Document Canvas */}
        <div className={`document-container ${showPreview ? 'with-preview' : ''}`}>
          <div className="document-paper">
            <textarea
              ref={editorRef}
              value={content}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              onSelect={handleSelectionChange}
              onMouseUp={handleSelectionChange}
              className="document-textarea"
              placeholder="Start typing your template...

Use {{ to insert data fields
Type / for commands  
Press Ctrl+I for inline AI editing
Select text for quick AI actions"
              spellCheck={false}
            />
          </div>
          
          {/* Hints bar */}
          <div className="editor-hints">
            <span><kbd>{"{{ }}"}</kbd> Insert field</span>
            <span><kbd>/</kbd> Commands</span>
            <span><kbd>Ctrl+I</kbd> AI Edit</span>
            <span>Select text for quick actions</span>
          </div>
        </div>
        
        {/* Preview Panel */}
        {showPreview && (
          <PreviewPanel content={content} sampleData={sampleData} />
        )}
      </div>
      
      {/* Selection Toolbar (Canvas-style) */}
      <SelectionToolbar
        state={selectionToolbar}
        onQuickAction={handleQuickAction}
        onCustomPrompt={handleCustomPromptFromToolbar}
        onClose={() => setSelectionToolbar(prev => ({ ...prev, visible: false }))}
      />
      
      {/* Completion Menu */}
      {completion && (
        <CompletionMenu
          completion={completion}
          onSelect={handleCompletionSelect}
          onClose={() => setCompletion(null)}
        />
      )}
      
      {/* AI Inline Editor */}
      <AIInlineEditor
        state={aiState}
        onSubmit={handleAISubmit}
        onCancel={handleAICancel}
        onAccept={handleAIAccept}
        onPromptChange={(prompt) => setAiState(prev => ({ ...prev, prompt }))}
      />
    </div>
  )
}

export default DocumentEditor
