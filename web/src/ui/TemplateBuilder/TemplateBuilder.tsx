/**
 * Template Builder - Main Component
 * 
 * Hybrid AI-Assisted Visual Template Designer
 * Combines agentic AI generation with precise visual control
 */

import React, { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Save, Undo2, Redo2, Settings, Eye, Code, Layout, Sparkles,
  FileText, ChevronLeft, ChevronRight, Download, Upload, X, Check,
  Loader2, AlertTriangle, HelpCircle, Maximize2, PanelLeftClose, PanelRightClose
} from 'lucide-react'
import { BuilderProvider, useBuilder, useBuilderKeyboard } from './BuilderState'
import { TemplateCanvas } from './TemplateCanvas'
import { FieldPalette } from './FieldPalette'
import { PropertiesPanel } from './PropertiesPanel'
import { TemplatePreview } from './TemplatePreview'
import { AIAssistant, AIToggleButton } from './AIAssistant'
import {
  PortableTemplate, EntitySchema, BuilderMode,
  DEFAULT_TEMPLATE, SECTION_TYPE_LABELS
} from './types'

// ============== Fallback Entity Schemas ==============

const FALLBACK_SCHEMAS: Record<string, any> = {
  'kahua_AEC_RFI.RFI': {
    entity_def: 'kahua_AEC_RFI.RFI',
    display_name: 'RFI',
    description: 'Request for Information',
    attributes: [
      { path: 'Number', name: 'Number', label: 'RFI Number', type: 'string', format: 'text' },
      { path: 'Subject', name: 'Subject', label: 'Subject', type: 'string', format: 'text' },
      { path: 'Description', name: 'Description', label: 'Description', type: 'string', format: 'rich_text' },
      { path: 'Status.Name', name: 'Status', label: 'Status', type: 'string', format: 'text' },
      { path: 'Priority.Name', name: 'Priority', label: 'Priority', type: 'string', format: 'text' },
      { path: 'DateSubmitted', name: 'DateSubmitted', label: 'Date Submitted', type: 'string', format: 'date' },
      { path: 'DateRequired', name: 'DateRequired', label: 'Date Required', type: 'string', format: 'date' },
      { path: 'DateClosed', name: 'DateClosed', label: 'Date Closed', type: 'string', format: 'date' },
      { path: 'SubmittedBy.Name', name: 'SubmittedBy', label: 'Submitted By', type: 'string', format: 'text' },
      { path: 'AssignedTo.Name', name: 'AssignedTo', label: 'Assigned To', type: 'string', format: 'text' },
      { path: 'Question', name: 'Question', label: 'Question', type: 'string', format: 'rich_text' },
      { path: 'Answer', name: 'Answer', label: 'Answer', type: 'string', format: 'rich_text' },
      { path: 'CostImpact', name: 'CostImpact', label: 'Cost Impact', type: 'number', format: 'currency' },
      { path: 'ScheduleImpact', name: 'ScheduleImpact', label: 'Schedule Impact (Days)', type: 'number', format: 'number' },
    ],
    child_entities: []
  },
  'kahua_Contract.Contract': {
    entity_def: 'kahua_Contract.Contract',
    display_name: 'Contract',
    description: 'Construction Contract',
    attributes: [
      { path: 'Number', name: 'Number', label: 'Contract Number', type: 'string', format: 'text' },
      { path: 'Name', name: 'Name', label: 'Contract Name', type: 'string', format: 'text' },
      { path: 'Description', name: 'Description', label: 'Description', type: 'string', format: 'rich_text' },
      { path: 'Status.Name', name: 'Status', label: 'Status', type: 'string', format: 'text' },
      { path: 'ContractType.Name', name: 'ContractType', label: 'Contract Type', type: 'string', format: 'text' },
      { path: 'OriginalAmount', name: 'OriginalAmount', label: 'Original Amount', type: 'number', format: 'currency' },
      { path: 'ApprovedChanges', name: 'ApprovedChanges', label: 'Approved Changes', type: 'number', format: 'currency' },
      { path: 'RevisedAmount', name: 'RevisedAmount', label: 'Revised Amount', type: 'number', format: 'currency' },
      { path: 'StartDate', name: 'StartDate', label: 'Start Date', type: 'string', format: 'date' },
      { path: 'EndDate', name: 'EndDate', label: 'End Date', type: 'string', format: 'date' },
      { path: 'Vendor.Name', name: 'Vendor', label: 'Vendor', type: 'string', format: 'text' },
      { path: 'ProjectManager.Name', name: 'ProjectManager', label: 'Project Manager', type: 'string', format: 'text' },
    ],
    child_entities: [
      {
        path: 'Items',
        entity_def: 'kahua_Contract.ContractItem',
        display_name: 'Contract Items',
        attributes: [
          { path: 'Number', name: 'Number', label: 'Item Number', type: 'string', format: 'text' },
          { path: 'Description', name: 'Description', label: 'Description', type: 'string', format: 'text' },
          { path: 'Quantity', name: 'Quantity', label: 'Quantity', type: 'number', format: 'number' },
          { path: 'UnitPrice', name: 'UnitPrice', label: 'Unit Price', type: 'number', format: 'currency' },
          { path: 'Amount', name: 'Amount', label: 'Amount', type: 'number', format: 'currency' },
        ]
      }
    ]
  },
  'kahua_AEC_Submittal.Submittal': {
    entity_def: 'kahua_AEC_Submittal.Submittal',
    display_name: 'Submittal',
    description: 'Construction Submittal',
    attributes: [
      { path: 'Number', name: 'Number', label: 'Submittal Number', type: 'string', format: 'text' },
      { path: 'Subject', name: 'Subject', label: 'Subject', type: 'string', format: 'text' },
      { path: 'Description', name: 'Description', label: 'Description', type: 'string', format: 'rich_text' },
      { path: 'Status.Name', name: 'Status', label: 'Status', type: 'string', format: 'text' },
      { path: 'SubmittalType.Name', name: 'SubmittalType', label: 'Type', type: 'string', format: 'text' },
      { path: 'DateSubmitted', name: 'DateSubmitted', label: 'Date Submitted', type: 'string', format: 'date' },
      { path: 'DateRequired', name: 'DateRequired', label: 'Date Required', type: 'string', format: 'date' },
      { path: 'SubmittedBy.Name', name: 'SubmittedBy', label: 'Submitted By', type: 'string', format: 'text' },
      { path: 'AssignedTo.Name', name: 'AssignedTo', label: 'Assigned To', type: 'string', format: 'text' },
      { path: 'SpecSection', name: 'SpecSection', label: 'Spec Section', type: 'string', format: 'text' },
    ],
    child_entities: []
  },
  'kahua_AEC_ChangeOrder.ChangeOrder': {
    entity_def: 'kahua_AEC_ChangeOrder.ChangeOrder',
    display_name: 'Change Order',
    description: 'Contract Change Order',
    attributes: [
      { path: 'Number', name: 'Number', label: 'CO Number', type: 'string', format: 'text' },
      { path: 'Subject', name: 'Subject', label: 'Subject', type: 'string', format: 'text' },
      { path: 'Description', name: 'Description', label: 'Description', type: 'string', format: 'rich_text' },
      { path: 'Status.Name', name: 'Status', label: 'Status', type: 'string', format: 'text' },
      { path: 'Amount', name: 'Amount', label: 'Amount', type: 'number', format: 'currency' },
      { path: 'ScheduleImpact', name: 'ScheduleImpact', label: 'Schedule Impact (Days)', type: 'number', format: 'number' },
      { path: 'DateSubmitted', name: 'DateSubmitted', label: 'Date Submitted', type: 'string', format: 'date' },
      { path: 'DateApproved', name: 'DateApproved', label: 'Date Approved', type: 'string', format: 'date' },
      { path: 'Reason.Name', name: 'Reason', label: 'Reason', type: 'string', format: 'text' },
    ],
    child_entities: []
  },
  'kahua_AEC_PunchList.PunchListItem': {
    entity_def: 'kahua_AEC_PunchList.PunchListItem',
    display_name: 'Punch List Item',
    description: 'Punch List Item',
    attributes: [
      { path: 'Number', name: 'Number', label: 'Item Number', type: 'string', format: 'text' },
      { path: 'Description', name: 'Description', label: 'Description', type: 'string', format: 'text' },
      { path: 'Status.Name', name: 'Status', label: 'Status', type: 'string', format: 'text' },
      { path: 'Priority.Name', name: 'Priority', label: 'Priority', type: 'string', format: 'text' },
      { path: 'Location', name: 'Location', label: 'Location', type: 'string', format: 'text' },
      { path: 'AssignedTo.Name', name: 'AssignedTo', label: 'Assigned To', type: 'string', format: 'text' },
      { path: 'DateCreated', name: 'DateCreated', label: 'Date Created', type: 'string', format: 'date' },
      { path: 'DateDue', name: 'DateDue', label: 'Date Due', type: 'string', format: 'date' },
      { path: 'DateCompleted', name: 'DateCompleted', label: 'Date Completed', type: 'string', format: 'date' },
    ],
    child_entities: []
  },
}

function getFallbackSchema(entityDef: string): any | null {
  return FALLBACK_SCHEMAS[entityDef] || null
}

// ============== Top Toolbar ==============

interface BuilderToolbarProps {
  onClose?: () => void
}

function BuilderToolbar({ onClose }: BuilderToolbarProps) {
  const { state, dispatch, actions } = useBuilder()
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = useCallback(async () => {
    setIsSaving(true)
    dispatch({ type: 'SET_SAVING', payload: true })

    try {
      const response = await fetch('/api/template/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.template),
      })

      if (response.ok) {
        const result = await response.json()
        dispatch({ type: 'UPDATE_TEMPLATE_METADATA', payload: { id: result.id } })
        dispatch({ type: 'MARK_CLEAN' })
      } else {
        throw new Error('Save failed')
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to save template' })
    } finally {
      setIsSaving(false)
      dispatch({ type: 'SET_SAVING', payload: false })
    }
  }, [state.template, dispatch])

  return (
    <div className="builder-toolbar">
      {/* Left section - Template info */}
      <div className="toolbar-left">
        <div className="template-name-input">
          <input
            type="text"
            value={state.template.name}
            onChange={(e) => actions.updateMetadata({ name: e.target.value })}
            placeholder="Template name"
          />
          {state.isDirty && <span className="dirty-indicator" title="Unsaved changes">●</span>}
        </div>
      </div>

      {/* Center section - Mode switcher */}
      <div className="toolbar-center">
        <div className="mode-switcher">
          <button
            className={`mode-btn ${state.mode === 'design' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_MODE', payload: 'design' })}
          >
            <Layout size={16} />
            <span>Design</span>
          </button>
          <button
            className={`mode-btn ${state.mode === 'preview' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_MODE', payload: 'preview' })}
          >
            <Eye size={16} />
            <span>Preview</span>
          </button>
          <button
            className={`mode-btn ${state.mode === 'code' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_MODE', payload: 'code' })}
          >
            <Code size={16} />
            <span>JSON</span>
          </button>
        </div>
      </div>

      {/* Right section - Actions */}
      <div className="toolbar-right">
        <div className="toolbar-actions">
          <button
            className="toolbar-btn"
            onClick={actions.undo}
            disabled={state.history.past.length === 0}
            title="Undo (Ctrl+Z)"
          >
            <Undo2 size={16} />
          </button>
          <button
            className="toolbar-btn"
            onClick={actions.redo}
            disabled={state.history.future.length === 0}
            title="Redo (Ctrl+Shift+Z)"
          >
            <Redo2 size={16} />
          </button>

          <div className="toolbar-divider" />

          <AIToggleButton />

          <div className="toolbar-divider" />

          <button
            className="toolbar-btn primary"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
            <span>Save</span>
          </button>
          
          {onClose && (
            <>
              <div className="toolbar-divider" />
              <button
                className="toolbar-btn"
                onClick={onClose}
                title="Close Builder (Esc)"
              >
                <X size={16} />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ============== Entity Selector ==============

function EntitySelector() {
  const { state, dispatch, actions } = useBuilder()
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')

  // Common Kahua entities
  const commonEntities = [
    { entity_def: 'kahua_Contract.Contract', display_name: 'Contracts' },
    { entity_def: 'kahua_AEC_RFI.RFI', display_name: 'RFIs' },
    { entity_def: 'kahua_AEC_Submittal.Submittal', display_name: 'Submittals' },
    { entity_def: 'kahua_AEC_ChangeOrder.ChangeOrder', display_name: 'Change Orders' },
    { entity_def: 'kahua_AEC_PunchList.PunchListItem', display_name: 'Punch List Items' },
    { entity_def: 'kahua_AEC_DailyReport.DailyReport', display_name: 'Daily Reports' },
    { entity_def: 'kahua_Meeting.Meeting', display_name: 'Meetings' },
    { entity_def: 'kahua_Project.Project', display_name: 'Projects' },
    { entity_def: 'kahua_ContractInvoice.ContractInvoice', display_name: 'Invoices' },
  ]

  const entities = state.availableEntities.length > 0 ? state.availableEntities : commonEntities

  const filteredEntities = search
    ? entities.filter(e =>
        e.display_name.toLowerCase().includes(search.toLowerCase()) ||
        e.entity_def.toLowerCase().includes(search.toLowerCase())
      )
    : entities

  const handleSelect = useCallback(async (entityDef: string) => {
    actions.updateMetadata({ target_entity_def: entityDef })
    setIsOpen(false)

    // Load entity schema from API, with fallback to static schema
    try {
      const response = await fetch(`/api/template/schema/${encodeURIComponent(entityDef)}`)
      if (response.ok) {
        const schema = await response.json()
        dispatch({ type: 'SET_ENTITY_SCHEMA', payload: schema })
        return
      }
    } catch (error) {
      console.warn('Failed to load entity schema from API, using fallback:', error)
    }
    
    // Fallback: use static schema definitions
    const fallbackSchema = getFallbackSchema(entityDef)
    if (fallbackSchema) {
      dispatch({ type: 'SET_ENTITY_SCHEMA', payload: fallbackSchema })
    }
  }, [actions, dispatch])

  const currentEntity = entities.find(e => e.entity_def === state.template.target_entity_def)
  const hasEntity = !!state.template.target_entity_def

  return (
    <div className={`entity-selector ${!hasEntity ? 'highlight-required' : ''}`}>
      <div className="entity-selector-label">
        <span>Step 1: Data Source</span>
        {!hasEntity && <span className="required-badge">Required</span>}
      </div>
      <button className={`entity-selector-btn ${!hasEntity ? 'pulse-border' : ''}`} onClick={() => setIsOpen(!isOpen)}>
        <FileText size={14} />
        <span>{currentEntity?.display_name || 'Select Entity Type...'}</span>
        <ChevronRight size={14} className={isOpen ? 'rotate-90' : ''} />
      </button>
      {!hasEntity && (
        <p className="entity-hint">Choose what type of data this template will display</p>
      )}

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="entity-dropdown"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <input
              type="text"
              placeholder="Search entities..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
            <div className="entity-list">
              {filteredEntities.map(entity => (
                <button
                  key={entity.entity_def}
                  className={`entity-option ${entity.entity_def === state.template.target_entity_def ? 'selected' : ''}`}
                  onClick={() => handleSelect(entity.entity_def)}
                >
                  <span className="entity-name">{entity.display_name}</span>
                  <span className="entity-def">{entity.entity_def}</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ============== JSON Editor (Code Mode) ==============

function JSONEditor() {
  const { state, dispatch, actions } = useBuilder()
  const [jsonText, setJsonText] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setJsonText(JSON.stringify(state.template, null, 2))
  }, [state.template])

  const handleApply = useCallback(() => {
    try {
      const parsed = JSON.parse(jsonText)
      actions.setTemplate(parsed)
      setError(null)
    } catch (e) {
      setError((e as Error).message)
    }
  }, [jsonText, actions])

  return (
    <div className="json-editor">
      <div className="json-toolbar">
        <span className="json-title">Template JSON</span>
        {error && (
          <span className="json-error">
            <AlertTriangle size={14} />
            {error}
          </span>
        )}
        <button className="json-apply-btn" onClick={handleApply}>
          <Check size={14} />
          Apply Changes
        </button>
      </div>
      <textarea
        className="json-textarea"
        value={jsonText}
        onChange={(e) => setJsonText(e.target.value)}
        spellCheck={false}
      />
    </div>
  )
}

// ============== Main Builder Layout ==============

interface BuilderLayoutProps {
  onClose?: () => void
}

function BuilderLayout({ onClose }: BuilderLayoutProps) {
  const { state, dispatch } = useBuilder()
  const [leftPanelOpen, setLeftPanelOpen] = useState(true)
  const [rightPanelOpen, setRightPanelOpen] = useState(true)

  useBuilderKeyboard()
  
  // Handle Escape key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && onClose && !state.ai.isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose, state.ai.isOpen])

  return (
    <div className="builder-layout">
      <BuilderToolbar onClose={onClose} />

      <div className="builder-main">
        {/* Left panel - Field palette */}
        <AnimatePresence>
          {leftPanelOpen && state.mode === 'design' && (
            <motion.div
              className="builder-panel left"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: state.leftPanelWidth, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              style={{ width: state.leftPanelWidth }}
            >
              <div className="panel-header">
                <span>Fields</span>
                <button onClick={() => setLeftPanelOpen(false)}>
                  <PanelLeftClose size={16} />
                </button>
              </div>
              <EntitySelector />
              <FieldPalette />
            </motion.div>
          )}
        </AnimatePresence>

        {!leftPanelOpen && state.mode === 'design' && (
          <button className="panel-toggle left" onClick={() => setLeftPanelOpen(true)}>
            <ChevronRight size={16} />
          </button>
        )}

        {/* Center content */}
        <div className="builder-content">
          {state.mode === 'design' && <TemplateCanvas />}
          {state.mode === 'preview' && <TemplatePreview />}
          {state.mode === 'code' && <JSONEditor />}
        </div>

        {/* Right panel - Properties */}
        <AnimatePresence>
          {rightPanelOpen && state.mode === 'design' && (
            <motion.div
              className="builder-panel right"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: state.rightPanelWidth, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              style={{ width: state.rightPanelWidth }}
            >
              <div className="panel-header">
                <span>Properties</span>
                <button onClick={() => setRightPanelOpen(false)}>
                  <PanelRightClose size={16} />
                </button>
              </div>
              <PropertiesPanel />
            </motion.div>
          )}
        </AnimatePresence>

        {!rightPanelOpen && state.mode === 'design' && (
          <button className="panel-toggle right" onClick={() => setRightPanelOpen(true)}>
            <ChevronLeft size={16} />
          </button>
        )}

        {/* AI Assistant overlay */}
        <AnimatePresence>
          {state.ai.isOpen && <AIAssistant />}
        </AnimatePresence>
      </div>

      {/* Status bar */}
      <div className="builder-statusbar">
        <span>{state.template.sections.length} sections</span>
        <span>•</span>
        <span>{state.template.target_entity_def || 'No entity'}</span>
        {state.error && (
          <>
            <span>•</span>
            <span className="status-error">
              <AlertTriangle size={12} />
              {state.error}
            </span>
          </>
        )}
      </div>
    </div>
  )
}

// ============== Main Export ==============

interface TemplateBuilderProps {
  initialTemplate?: PortableTemplate
  onSave?: (template: PortableTemplate) => void
  onClose?: () => void
}

export function TemplateBuilder({ initialTemplate, onSave, onClose }: TemplateBuilderProps) {
  return (
    <BuilderProvider initialTemplate={initialTemplate}>
      <div className="template-builder">
        <BuilderLayout onClose={onClose} />
      </div>
    </BuilderProvider>
  )
}

export default TemplateBuilder
