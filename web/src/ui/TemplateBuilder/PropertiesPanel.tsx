/**
 * Properties Panel
 * 
 * Right sidebar for editing selected section/field properties
 */

import React, { useState, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Settings, ChevronDown, ChevronRight, Palette, Layout, Type, Table,
  List, FileText, Trash2, Plus, GripVertical, X, AlignLeft, AlignCenter, AlignRight
} from 'lucide-react'
import { useBuilder } from './BuilderState'
import {
  Section, SectionType, FieldMapping, FieldFormat, ColumnDef,
  Alignment, LayoutMode, SECTION_TYPE_LABELS, FORMAT_LABELS
} from './types'

// ============== Collapsible Panel ==============

interface PanelSectionProps {
  title: string
  icon?: React.ElementType
  defaultExpanded?: boolean
  children: React.ReactNode
}

function PanelSection({ title, icon: Icon, defaultExpanded = true, children }: PanelSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className={`panel-section ${isExpanded ? 'expanded' : ''}`}>
      <button className="panel-section-header" onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {Icon && <Icon size={14} />}
        <span>{title}</span>
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="panel-section-content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ============== Form Controls ==============

interface TextInputProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  multiline?: boolean
}

function TextInput({ label, value, onChange, placeholder, multiline }: TextInputProps) {
  return (
    <div className="form-field">
      <label>{label}</label>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={3}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
      )}
    </div>
  )
}

interface SelectInputProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
}

function SelectInput({ label, value, onChange, options }: SelectInputProps) {
  return (
    <div className="form-field">
      <label>{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

interface NumberInputProps {
  label: string
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
}

function NumberInput({ label, value, onChange, min, max, step = 1 }: NumberInputProps) {
  return (
    <div className="form-field">
      <label>{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        min={min}
        max={max}
        step={step}
      />
    </div>
  )
}

interface CheckboxInputProps {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
}

function CheckboxInput({ label, checked, onChange }: CheckboxInputProps) {
  return (
    <div className="form-field checkbox">
      <label>
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span>{label}</span>
      </label>
    </div>
  )
}

interface ColorInputProps {
  label: string
  value: string
  onChange: (value: string) => void
}

function ColorInput({ label, value, onChange }: ColorInputProps) {
  return (
    <div className="form-field color">
      <label>{label}</label>
      <div className="color-input-wrapper">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#000000"
        />
      </div>
    </div>
  )
}

// ============== Field Editor ==============

interface FieldEditorProps {
  field: FieldMapping
  index: number
  sectionId: string
  onUpdate: (index: number, updates: Partial<FieldMapping>) => void
  onDelete: (index: number) => void
  onMove: (fromIndex: number, toIndex: number) => void
}

function FieldEditor({ field, index, sectionId, onUpdate, onDelete, onMove }: FieldEditorProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className={`field-editor ${isExpanded ? 'expanded' : ''}`}>
      <div className="field-editor-header">
        <div className="field-drag-handle">
          <GripVertical size={12} />
        </div>
        <button
          className="field-expand-btn"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </button>
        <span className="field-path-display">{field.label || field.path}</span>
        <span className={`field-format-badge format-${field.format}`}>
          {field.format}
        </span>
        <button
          className="field-delete-btn"
          onClick={() => onDelete(index)}
        >
          <X size={12} />
        </button>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="field-editor-details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            <TextInput
              label="Field Path"
              value={field.path}
              onChange={(value) => onUpdate(index, { path: value })}
              placeholder="e.g., Status.Name"
            />
            <TextInput
              label="Label"
              value={field.label || ''}
              onChange={(value) => onUpdate(index, { label: value })}
              placeholder="Display label"
            />
            <SelectInput
              label="Format"
              value={field.format}
              onChange={(value) => onUpdate(index, { format: value as FieldFormat })}
              options={Object.entries(FORMAT_LABELS).map(([value, label]) => ({ value, label }))}
            />
            <TextInput
              label="Default Value"
              value={field.default_value || ''}
              onChange={(value) => onUpdate(index, { default_value: value || undefined })}
              placeholder="Fallback if empty"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ============== Column Editor (for Tables) ==============

interface ColumnEditorProps {
  column: ColumnDef
  sectionId: string
  onUpdate: (columnId: string, updates: Partial<ColumnDef>) => void
  onDelete: (columnId: string) => void
}

function ColumnEditor({ column, sectionId, onUpdate, onDelete }: ColumnEditorProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className={`column-editor ${isExpanded ? 'expanded' : ''}`}>
      <div className="column-editor-header">
        <div className="column-drag-handle">
          <GripVertical size={12} />
        </div>
        <button
          className="column-expand-btn"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </button>
        <span className="column-label-display">{column.field.label || column.field.path}</span>
        <div className="column-alignment">
          <button
            className={column.alignment === 'left' ? 'active' : ''}
            onClick={() => onUpdate(column.id, { alignment: 'left' })}
          >
            <AlignLeft size={12} />
          </button>
          <button
            className={column.alignment === 'center' ? 'active' : ''}
            onClick={() => onUpdate(column.id, { alignment: 'center' })}
          >
            <AlignCenter size={12} />
          </button>
          <button
            className={column.alignment === 'right' ? 'active' : ''}
            onClick={() => onUpdate(column.id, { alignment: 'right' })}
          >
            <AlignRight size={12} />
          </button>
        </div>
        <button
          className="column-delete-btn"
          onClick={() => onDelete(column.id)}
        >
          <X size={12} />
        </button>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="column-editor-details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            <TextInput
              label="Field Path"
              value={column.field.path}
              onChange={(value) => onUpdate(column.id, {
                field: { ...column.field, path: value }
              })}
            />
            <TextInput
              label="Header Label"
              value={column.field.label || ''}
              onChange={(value) => onUpdate(column.id, {
                field: { ...column.field, label: value }
              })}
            />
            <SelectInput
              label="Format"
              value={column.field.format}
              onChange={(value) => onUpdate(column.id, {
                field: { ...column.field, format: value as FieldFormat }
              })}
              options={Object.entries(FORMAT_LABELS).map(([value, label]) => ({ value, label }))}
            />
            <NumberInput
              label="Width (%)"
              value={column.width || 0}
              onChange={(value) => onUpdate(column.id, { width: value || undefined })}
              min={0}
              max={100}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ============== Section-specific Panels ==============

function HeaderSectionPanel({ section }: { section: Section }) {
  const { actions } = useBuilder()
  const config = section.header_config!

  return (
    <>
      <PanelSection title="Layout" icon={Layout}>
        <SelectInput
          label="Field Layout"
          value={config.layout}
          onChange={(value) => actions.updateSection(section.id, {
            header_config: { ...config, layout: value as LayoutMode }
          })}
          options={[
            { value: 'horizontal', label: 'Horizontal' },
            { value: 'vertical', label: 'Vertical' },
            { value: 'grid', label: 'Grid' },
          ]}
        />
        {config.layout === 'grid' && (
          <NumberInput
            label="Columns"
            value={config.columns}
            onChange={(value) => actions.updateSection(section.id, {
              header_config: { ...config, columns: value }
            })}
            min={1}
            max={4}
          />
        )}
        <CheckboxInput
          label="Show Labels"
          checked={config.show_labels}
          onChange={(checked) => actions.updateSection(section.id, {
            header_config: { ...config, show_labels: checked }
          })}
        />
      </PanelSection>

      <PanelSection title="Title Template" icon={Type}>
        <TextInput
          label="Template"
          value={config.title_template || ''}
          onChange={(value) => actions.updateSection(section.id, {
            header_config: { ...config, title_template: value || undefined }
          })}
          placeholder="{Number} - {Description}"
        />
        <p className="hint">Use {'{FieldPath}'} for dynamic values</p>
      </PanelSection>

      <PanelSection title="Fields" icon={List}>
        <div className="fields-list">
          {config.fields.map((field, index) => (
            <FieldEditor
              key={index}
              field={field}
              index={index}
              sectionId={section.id}
              onUpdate={(i, updates) => actions.updateField(section.id, i, updates)}
              onDelete={(i) => actions.deleteField(section.id, i)}
              onMove={(from, to) => actions.moveField(section.id, from, to)}
            />
          ))}
        </div>
        <button
          className="add-field-btn"
          onClick={() => actions.addField(section.id, {
            path: '',
            format: 'text',
          })}
        >
          <Plus size={14} />
          Add Field
        </button>
      </PanelSection>
    </>
  )
}

function DetailSectionPanel({ section }: { section: Section }) {
  const { actions } = useBuilder()
  const config = section.detail_config!

  return (
    <>
      <PanelSection title="Layout" icon={Layout}>
        <SelectInput
          label="Field Layout"
          value={config.layout}
          onChange={(value) => actions.updateSection(section.id, {
            detail_config: { ...config, layout: value as LayoutMode }
          })}
          options={[
            { value: 'horizontal', label: 'Horizontal' },
            { value: 'vertical', label: 'Vertical' },
            { value: 'grid', label: 'Grid' },
          ]}
        />
        {config.layout === 'grid' && (
          <NumberInput
            label="Columns"
            value={config.columns}
            onChange={(value) => actions.updateSection(section.id, {
              detail_config: { ...config, columns: value }
            })}
            min={1}
            max={4}
          />
        )}
        <CheckboxInput
          label="Show Labels"
          checked={config.show_labels}
          onChange={(checked) => actions.updateSection(section.id, {
            detail_config: { ...config, show_labels: checked }
          })}
        />
      </PanelSection>

      <PanelSection title="Fields" icon={List}>
        <div className="fields-list">
          {config.fields.map((field, index) => (
            <FieldEditor
              key={index}
              field={field}
              index={index}
              sectionId={section.id}
              onUpdate={(i, updates) => actions.updateField(section.id, i, updates)}
              onDelete={(i) => actions.deleteField(section.id, i)}
              onMove={(from, to) => actions.moveField(section.id, from, to)}
            />
          ))}
        </div>
        <button
          className="add-field-btn"
          onClick={() => actions.addField(section.id, {
            path: '',
            format: 'text',
          })}
        >
          <Plus size={14} />
          Add Field
        </button>
      </PanelSection>
    </>
  )
}

function TableSectionPanel({ section }: { section: Section }) {
  const { actions } = useBuilder()
  const config = section.table_config!

  return (
    <>
      <PanelSection title="Data Source" icon={Table}>
        <TextInput
          label="Source Path"
          value={config.source}
          onChange={(value) => actions.updateSection(section.id, {
            table_config: { ...config, source: value }
          })}
          placeholder="e.g., Items, References"
        />
        <TextInput
          label="Entity Type (optional)"
          value={config.entity_def || ''}
          onChange={(value) => actions.updateSection(section.id, {
            table_config: { ...config, entity_def: value || undefined }
          })}
          placeholder="e.g., kahua_Contract.ContractItem"
        />
      </PanelSection>

      <PanelSection title="Options" icon={Settings}>
        <CheckboxInput
          label="Show Header Row"
          checked={config.show_header}
          onChange={(checked) => actions.updateSection(section.id, {
            table_config: { ...config, show_header: checked }
          })}
        />
        <CheckboxInput
          label="Show Row Numbers"
          checked={config.show_row_numbers}
          onChange={(checked) => actions.updateSection(section.id, {
            table_config: { ...config, show_row_numbers: checked }
          })}
        />
        <CheckboxInput
          label="Show Subtotals"
          checked={config.show_subtotals}
          onChange={(checked) => actions.updateSection(section.id, {
            table_config: { ...config, show_subtotals: checked }
          })}
        />
        <TextInput
          label="Empty Message"
          value={config.empty_message}
          onChange={(value) => actions.updateSection(section.id, {
            table_config: { ...config, empty_message: value }
          })}
          placeholder="No items"
        />
      </PanelSection>

      <PanelSection title="Sorting" icon={List}>
        <TextInput
          label="Sort By"
          value={config.sort_by || ''}
          onChange={(value) => actions.updateSection(section.id, {
            table_config: { ...config, sort_by: value || undefined }
          })}
          placeholder="Field path to sort by"
        />
        <SelectInput
          label="Direction"
          value={config.sort_direction}
          onChange={(value) => actions.updateSection(section.id, {
            table_config: { ...config, sort_direction: value as 'asc' | 'desc' }
          })}
          options={[
            { value: 'asc', label: 'Ascending' },
            { value: 'desc', label: 'Descending' },
          ]}
        />
      </PanelSection>

      <PanelSection title="Columns" icon={Table}>
        <div className="columns-list">
          {config.columns.map((column) => (
            <ColumnEditor
              key={column.id}
              column={column}
              sectionId={section.id}
              onUpdate={(colId, updates) => actions.updateColumn(section.id, colId, updates)}
              onDelete={(colId) => actions.deleteColumn(section.id, colId)}
            />
          ))}
        </div>
        <button
          className="add-column-btn"
          onClick={() => actions.addColumn(section.id, {
            id: `col-${Date.now()}`,
            field: { path: '', format: 'text' },
            alignment: 'left',
          })}
        >
          <Plus size={14} />
          Add Column
        </button>
      </PanelSection>
    </>
  )
}

function TextSectionPanel({ section }: { section: Section }) {
  const { actions } = useBuilder()
  const config = section.text_config!

  return (
    <PanelSection title="Content" icon={Type}>
      <TextInput
        label="Text Content"
        value={config.content}
        onChange={(value) => actions.updateSection(section.id, {
          text_config: { ...config, content: value }
        })}
        placeholder="Enter text or use {FieldPath} for dynamic values"
        multiline
      />
      <p className="hint">Use {'{FieldPath}'} to include entity field values</p>
    </PanelSection>
  )
}

// ============== Main Properties Panel ==============

export function PropertiesPanel() {
  const { state, dispatch, actions } = useBuilder()

  // Get selected section
  const selectedSection = useMemo(() => {
    if (state.selection.type !== 'section' || !state.selection.id) return null
    return state.template.sections.find(s => s.id === state.selection.id)
  }, [state.selection, state.template.sections])

  if (!selectedSection) {
    return (
      <div className="properties-panel empty">
        <div className="no-selection-state">
          <div className="no-selection-icon">
            <Settings size={28} />
          </div>
          <h4>No Section Selected</h4>
          <p>
            {state.template.sections.length === 0 
              ? "Add a section to get started, then select it to configure its properties here."
              : "Click on a section in the canvas to select it and edit its properties here."
            }
          </p>
          {state.template.sections.length > 0 && (
            <div className="selection-hint">
              <span className="hint-arrow">←</span>
              <span>Click any section card</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="properties-panel">
      {/* Section header */}
      <div className="properties-header">
        <span className="section-type-badge">
          {SECTION_TYPE_LABELS[selectedSection.type]}
        </span>
        <div className="properties-actions">
          <button
            className="danger"
            onClick={() => actions.deleteSection(selectedSection.id)}
            title="Delete section"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Section title */}
      <PanelSection title="Section" icon={FileText}>
        <TextInput
          label="Title"
          value={selectedSection.title || ''}
          onChange={(value) => actions.updateSection(selectedSection.id, { title: value || undefined })}
          placeholder="Optional section title"
        />
      </PanelSection>

      {/* Type-specific panels */}
      {selectedSection.type === 'header' && selectedSection.header_config && (
        <HeaderSectionPanel section={selectedSection} />
      )}
      {selectedSection.type === 'detail' && selectedSection.detail_config && (
        <DetailSectionPanel section={selectedSection} />
      )}
      {selectedSection.type === 'table' && selectedSection.table_config && (
        <TableSectionPanel section={selectedSection} />
      )}
      {selectedSection.type === 'text' && selectedSection.text_config && (
        <TextSectionPanel section={selectedSection} />
      )}

      {/* Styling */}
      <PanelSection title="Styling" icon={Palette} defaultExpanded={false}>
        <ColorInput
          label="Background Color"
          value={selectedSection.background_color || '#ffffff'}
          onChange={(value) => actions.updateSection(selectedSection.id, {
            background_color: value === '#ffffff' ? undefined : value
          })}
        />
      </PanelSection>
    </div>
  )
}

export default PropertiesPanel
