/**
 * Template Builder Canvas
 * 
 * Main visual canvas for designing templates with drag-drop sections
 */

import React, { useCallback, useRef, useState } from 'react'
import { motion, AnimatePresence, Reorder, useDragControls } from 'framer-motion'
import {
  GripVertical, Plus, Trash2, Copy, Settings, ChevronDown, ChevronRight,
  FileText, List, Table, Type, Image, BarChart, Edit3, Minus, Layers,
  MoreHorizontal, Eye, EyeOff, Lock, Unlock, Sparkles, HelpCircle
} from 'lucide-react'
import { useBuilder, useBuilderKeyboard } from './BuilderState'
import {
  Section, SectionType, FieldMapping, ColumnDef,
  SECTION_TYPE_LABELS, SECTION_TYPE_ICONS
} from './types'

// Icon mapping
const SectionIcons: Record<string, React.ElementType> = {
  FileText, List, Table, AlignLeft: Type, Image, BarChart, Edit3, Minus, Layers
}

function getSectionIcon(type: SectionType): React.ElementType {
  const iconName = SECTION_TYPE_ICONS[type]
  return SectionIcons[iconName] || FileText
}

// ============== Section Card ==============

interface SectionCardProps {
  section: Section
  isSelected: boolean
  isHovered: boolean
  onSelect: () => void
  onDelete: () => void
  onDuplicate: () => void
}

function SectionCard({ section, isSelected, isHovered, onSelect, onDelete, onDuplicate }: SectionCardProps) {
  const { state, dispatch, actions } = useBuilder()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const dragControls = useDragControls()

  const Icon = getSectionIcon(section.type)
  const label = SECTION_TYPE_LABELS[section.type]

  // Get field count
  const getFieldCount = () => {
    if (section.header_config) return section.header_config.fields.length
    if (section.detail_config) return section.detail_config.fields.length
    if (section.table_config) return section.table_config.columns.length
    return 0
  }

  return (
    <Reorder.Item
      value={section}
      id={section.id}
      dragListener={false}
      dragControls={dragControls}
      className={`section-card ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
      onClick={onSelect}
      onMouseEnter={() => dispatch({ type: 'SET_HOVERED', payload: section.id })}
      onMouseLeave={() => dispatch({ type: 'SET_HOVERED', payload: null })}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20, height: 0 }}
      transition={{ duration: 0.2 }}
    >
      {/* Header */}
      <div className="section-card-header">
        <div
          className="section-drag-handle"
          onPointerDown={(e) => dragControls.start(e)}
        >
          <GripVertical size={14} />
        </div>

        <button
          className="section-collapse-btn"
          onClick={(e) => {
            e.stopPropagation()
            setIsCollapsed(!isCollapsed)
          }}
        >
          {isCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
        </button>

        <div className="section-icon">
          <Icon size={16} />
        </div>

        <div className="section-info">
          <span className="section-type">{label}</span>
          {section.title && <span className="section-title">{section.title}</span>}
        </div>

        <div className="section-badges">
          {getFieldCount() > 0 && (
            <span className="field-count">{getFieldCount()} fields</span>
          )}
        </div>

        <div className="section-actions">
          <button
            className="section-action-btn"
            onClick={(e) => {
              e.stopPropagation()
              onDuplicate()
            }}
            title="Duplicate"
          >
            <Copy size={14} />
          </button>
          <button
            className="section-action-btn danger"
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
            title="Delete"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Content preview */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            className="section-card-content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <SectionPreview section={section} />
          </motion.div>
        )}
      </AnimatePresence>
    </Reorder.Item>
  )
}

// ============== Section Preview ==============

function SectionPreview({ section }: { section: Section }) {
  if (section.type === 'header' && section.header_config) {
    return (
      <div className="section-preview header-preview">
        {section.header_config.title_template && (
          <div className="preview-title-template">
            {section.header_config.title_template}
          </div>
        )}
        <div className={`preview-fields layout-${section.header_config.layout}`}>
          {section.header_config.fields.map((field, i) => (
            <FieldPill key={i} field={field} />
          ))}
        </div>
      </div>
    )
  }

  if (section.type === 'detail' && section.detail_config) {
    return (
      <div className="section-preview detail-preview">
        <div className={`preview-fields layout-${section.detail_config.layout}`}>
          {section.detail_config.fields.map((field, i) => (
            <FieldPill key={i} field={field} showLabel />
          ))}
        </div>
      </div>
    )
  }

  if (section.type === 'table' && section.table_config) {
    return (
      <div className="section-preview table-preview">
        <div className="preview-table-header">
          {section.table_config.columns.map((col, i) => (
            <div key={i} className="preview-column-header">
              {col.field.label || col.field.path}
            </div>
          ))}
        </div>
        <div className="preview-table-body">
          <div className="preview-table-row placeholder">
            {section.table_config.columns.map((_, i) => (
              <div key={i} className="preview-cell-placeholder" />
            ))}
          </div>
        </div>
        <div className="preview-table-meta">
          Source: <code>{section.table_config.source}</code>
          {section.table_config.show_subtotals && (
            <span className="subtotals-indicator">+ Subtotals</span>
          )}
        </div>
      </div>
    )
  }

  if (section.type === 'text' && section.text_config) {
    return (
      <div className="section-preview text-preview">
        <div className="preview-text-content">
          {section.text_config.content.length > 100
            ? section.text_config.content.substring(0, 100) + '...'
            : section.text_config.content
          }
        </div>
      </div>
    )
  }

  if (section.type === 'chart' && section.chart_config) {
    return (
      <div className="section-preview chart-preview">
        <div className="preview-chart-placeholder">
          <BarChart size={24} />
          <span>{section.chart_config.chart_type} chart</span>
        </div>
        <div className="preview-chart-meta">
          Labels: {section.chart_config.label_field} | Values: {section.chart_config.value_field}
        </div>
      </div>
    )
  }

  if (section.type === 'page_break') {
    return (
      <div className="section-preview page-break-preview">
        <div className="page-break-line" />
        <span>Page Break</span>
        <div className="page-break-line" />
      </div>
    )
  }

  return (
    <div className="section-preview empty-preview">
      <span className="empty-text">Configure this section in the properties panel</span>
    </div>
  )
}

// ============== Field Pill ==============

function FieldPill({ field, showLabel = false }: { field: FieldMapping; showLabel?: boolean }) {
  return (
    <div className="field-pill" title={field.path}>
      {showLabel && field.label && (
        <span className="field-label">{field.label}:</span>
      )}
      <span className="field-path">{field.path}</span>
      <span className={`field-format format-${field.format}`}>
        {field.format}
      </span>
    </div>
  )
}

// ============== Add Section Button ==============

function AddSectionButton({ onAdd }: { onAdd: (type: SectionType) => void }) {
  const [isOpen, setIsOpen] = useState(false)

  const sectionTypes: { type: SectionType; icon: React.ElementType; description: string; recommended?: boolean }[] = [
    { type: 'header', icon: FileText, description: 'Title and identifying information', recommended: true },
    { type: 'detail', icon: List, description: 'Key-value field pairs', recommended: true },
    { type: 'table', icon: Table, description: 'Data table from child collection', recommended: true },
    { type: 'text', icon: Type, description: 'Static or dynamic text' },
    { type: 'chart', icon: BarChart, description: 'Visual data chart' },
    { type: 'page_break', icon: Minus, description: 'Force new page' },
  ]

  return (
    <div className="add-section-container">
      <button
        className="add-section-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Plus size={18} />
        <span>Add Section</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop to close menu */}
            <motion.div 
              className="add-section-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              className="add-section-menu"
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
            >
              <div className="menu-header">
                <span>Choose section type</span>
                <HelpCircle size={14} />
              </div>
              {sectionTypes.map(({ type, icon: Icon, description, recommended }) => (
                <button
                  key={type}
                  className={`add-section-option ${recommended ? 'recommended' : ''}`}
                  onClick={() => {
                    onAdd(type)
                    setIsOpen(false)
                  }}
                >
                  <div className="option-icon">
                    <Icon size={20} />
                  </div>
                  <div className="option-info">
                    <span className="option-label">
                      {SECTION_TYPE_LABELS[type]}
                      {recommended && <span className="recommended-badge">Common</span>}
                    </span>
                    <span className="option-description">{description}</span>
                  </div>
                </button>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

// ============== Empty State ==============

function EmptyCanvas({ onAddSection }: { onAddSection: (type: SectionType) => void }) {
  const { state, dispatch } = useBuilder()
  const hasEntity = !!state.template.target_entity_def
  const entityName = hasEntity 
    ? (state.entitySchema?.display_name || state.template.target_entity_def.split('.').pop())
    : null
  
  return (
    <div className="empty-canvas">
      <div className="empty-canvas-content">
        {/* Welcome header */}
        <div className="welcome-header">
          <div className="welcome-icon">
            <FileText size={36} />
          </div>
          <h2>Design Your Report Template</h2>
          <p className="welcome-subtitle">
            Create professional documents in minutes with our visual builder
          </p>
        </div>

        {/* Step-by-step guide */}
        <div className="onboarding-steps">
          {/* Step 1: Select Entity */}
          <div className={`onboarding-step ${hasEntity ? 'completed' : 'active'}`}>
            <div className="step-number">{hasEntity ? '✓' : '1'}</div>
            <div className="step-content">
              <h4>Choose Your Data Source</h4>
              <p>What type of record will this template display?</p>
              {!hasEntity && (
                <div className="step-hint">
                  <span className="hint-arrow">←</span>
                  Select an entity type from the Fields panel
                </div>
              )}
              {hasEntity && entityName && (
                <div className="step-complete-badge">
                  <span>✓ {entityName}</span>
                </div>
              )}
            </div>
          </div>

          {/* Step 2: Add Sections */}
          <div className={`onboarding-step ${hasEntity ? 'active' : 'upcoming'}`}>
            <div className="step-number">2</div>
            <div className="step-content">
              <h4>Add Layout Sections</h4>
              <p>Build your document structure with these common sections:</p>
              
              {hasEntity && (
                <div className="quick-start-grid">
                  <button
                    className="quick-start-card"
                    onClick={() => onAddSection('header')}
                  >
                    <div className="card-icon"><FileText size={22} /></div>
                    <div className="card-info">
                      <span className="card-title">Header</span>
                      <span className="card-desc">Title & key info</span>
                    </div>
                  </button>
                  <button
                    className="quick-start-card"
                    onClick={() => onAddSection('detail')}
                  >
                    <div className="card-icon"><List size={22} /></div>
                    <div className="card-info">
                      <span className="card-title">Details</span>
                      <span className="card-desc">Field-value pairs</span>
                    </div>
                  </button>
                  <button
                    className="quick-start-card"
                    onClick={() => onAddSection('table')}
                  >
                    <div className="card-icon"><Table size={22} /></div>
                    <div className="card-info">
                      <span className="card-title">Table</span>
                      <span className="card-desc">List of items</span>
                    </div>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Step 3: Configure */}
          <div className="onboarding-step upcoming">
            <div className="step-number">3</div>
            <div className="step-content">
              <h4>Drag Fields & Customize</h4>
              <p>Drag fields onto sections, then fine-tune in the Properties panel</p>
            </div>
          </div>
        </div>

        {/* AI Alternative */}
        <div className="ai-alternative">
          <div className="divider-with-text">
            <span>or use AI</span>
          </div>
          <button 
            className="ai-cta-button"
            onClick={() => dispatch({ type: 'TOGGLE_AI', payload: true })}
          >
            <Sparkles size={18} />
            <span>Let AI build your template from a description</span>
          </button>
        </div>
      </div>
    </div>
  )
}

// ============== Main Canvas Component ==============

export function TemplateCanvas() {
  const { state, dispatch, actions } = useBuilder()
  useBuilderKeyboard()

  const handleAddSection = useCallback((type: SectionType, afterId?: string) => {
    const newSection: Section = {
      id: `section-${Date.now()}`,
      type,
      order: state.template.sections.length,
      // Initialize with type-specific config
      ...(type === 'header' && {
        header_config: {
          fields: [],
          layout: 'grid' as const,
          columns: 2,
          show_labels: true,
        },
      }),
      ...(type === 'detail' && {
        detail_config: {
          fields: [],
          layout: 'grid' as const,
          columns: 2,
          show_labels: true,
        },
      }),
      ...(type === 'table' && {
        table_config: {
          source: 'Items',
          columns: [],
          show_header: true,
          show_row_numbers: false,
          sort_direction: 'asc' as const,
          show_subtotals: false,
          subtotal_fields: [],
          empty_message: 'No items',
        },
      }),
      ...(type === 'text' && {
        text_config: {
          content: '',
        },
      }),
      ...(type === 'chart' && {
        chart_config: {
          chart_type: 'bar' as const,
          title: 'Chart',
          data_source: '',
          label_field: '',
          value_field: '',
          width: 6.0,
          height: 4.0,
          show_legend: true,
          show_values: true,
        },
      }),
    }

    actions.addSection(newSection, afterId)
  }, [state.template.sections.length, actions])

  const handleReorder = useCallback((newOrder: Section[]) => {
    // Update section order
    newOrder.forEach((section, index) => {
      if (section.order !== index) {
        actions.updateSection(section.id, { order: index })
      }
    })
  }, [actions])

  if (state.template.sections.length === 0) {
    return <EmptyCanvas onAddSection={handleAddSection} />
  }

  return (
    <div className="template-canvas">
      {/* Document info bar */}
      <div className="canvas-header">
        <div className="document-orientation">
          {state.template.layout.orientation === 'portrait' ? '📄' : '📃'} 
          {state.template.layout.orientation}
        </div>
        <div className="document-entity">
          {state.template.target_entity_def || 'No entity selected'}
        </div>
      </div>

      {/* Sections list */}
      <Reorder.Group
        axis="y"
        values={state.template.sections}
        onReorder={handleReorder}
        className="sections-list"
      >
        <AnimatePresence>
          {state.template.sections
            .sort((a, b) => a.order - b.order)
            .map((section) => (
              <SectionCard
                key={section.id}
                section={section}
                isSelected={state.selection.type === 'section' && state.selection.id === section.id}
                isHovered={state.hoveredId === section.id}
                onSelect={() => actions.select({ type: 'section', id: section.id })}
                onDelete={() => actions.deleteSection(section.id)}
                onDuplicate={() => actions.duplicateSection(section.id)}
              />
            ))}
        </AnimatePresence>
      </Reorder.Group>

      {/* Add section button */}
      <AddSectionButton onAdd={handleAddSection} />
    </div>
  )
}

export default TemplateCanvas
