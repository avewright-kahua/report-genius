/**
 * Field Palette Panel
 * 
 * Left sidebar showing available entity attributes that can be dragged into sections
 */

import React, { useState, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, ChevronDown, ChevronRight, Grip, Database, Calendar, DollarSign,
  Hash, Type, ToggleLeft, Link, Image, FileText, List, Folder, FolderOpen
} from 'lucide-react'
import { useBuilder } from './BuilderState'
import { EntityAttribute, EntitySchema, FieldFormat, FieldMapping, FORMAT_LABELS } from './types'

// Format icons
const FormatIcons: Record<FieldFormat, React.ElementType> = {
  text: Type,
  number: Hash,
  currency: DollarSign,
  date: Calendar,
  datetime: Calendar,
  percent: Hash,
  boolean: ToggleLeft,
  rich_text: FileText,
  image: Image,
  url: Link,
}

// ============== Draggable Field Item ==============

interface FieldItemProps {
  attribute: EntityAttribute
  onDragStart: () => void
  onDragEnd: () => void
  onDoubleClick: () => void
  canAdd: boolean
}

function FieldItem({ attribute, onDragStart, onDragEnd, onDoubleClick, canAdd }: FieldItemProps) {
  const [isDragging, setIsDragging] = useState(false)
  const Icon = FormatIcons[attribute.format] || Type

  const handleDragStart = useCallback((e: React.DragEvent) => {
    setIsDragging(true)
    onDragStart()
    // Set drag data
    e.dataTransfer.setData('application/json', JSON.stringify({
      type: 'new-field',
      attribute,
    }))
    e.dataTransfer.effectAllowed = 'copy'
  }, [attribute, onDragStart])

  return (
    <motion.div
      className={`field-item ${isDragging ? 'dragging' : ''}`}
      draggable
      onDragStart={handleDragStart as any}
      onDragEnd={() => {
        setIsDragging(false)
        onDragEnd()
      }}
      title={`${attribute.path}\n${attribute.description || ''}`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className="field-item-drag">
        <Grip size={12} />
      </div>
      <div className="field-item-icon">
        <Icon size={14} />
      </div>
      <div className="field-item-info">
        <span className="field-item-name">{attribute.label || attribute.name}</span>
        <span className="field-item-path">{attribute.path}</span>
      </div>
      <div className={`field-item-type format-${attribute.format}`}>
        {FORMAT_LABELS[attribute.format]}
      </div>
      {canAdd && (
        <button 
          className="field-add-btn"
          onClick={(e) => {
            e.stopPropagation()
            onDoubleClick()
          }}
          title="Add to selected section"
        >
          +
        </button>
      )}
    </motion.div>
  )
}

// ============== Field Group (Collapsible) ==============

interface FieldGroupProps {
  title: string
  icon: React.ElementType
  fields: EntityAttribute[]
  isExpanded: boolean
  onToggle: () => void
  onFieldDragStart: (attr: EntityAttribute) => void
  onFieldDragEnd: () => void
  onFieldDoubleClick: (attr: EntityAttribute) => void
  canAddToSection: boolean
}

function FieldGroup({
  title, icon: Icon, fields, isExpanded, onToggle,
  onFieldDragStart, onFieldDragEnd, onFieldDoubleClick, canAddToSection
}: FieldGroupProps) {
  return (
    <div className={`field-group ${isExpanded ? 'expanded' : ''}`}>
      <button className="field-group-header" onClick={onToggle}>
        <span className="field-group-chevron">
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
        <span className="field-group-icon">
          <Icon size={16} />
        </span>
        <span className="field-group-title">{title}</span>
        <span className="field-group-count">{fields.length}</span>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="field-group-content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {fields.map((field) => (
              <FieldItem
                key={field.path}
                attribute={field}
                onDragStart={() => onFieldDragStart(field)}
                onDragEnd={onFieldDragEnd}
                onDoubleClick={() => onFieldDoubleClick(field)}
                canAdd={canAddToSection}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ============== Child Entity Section ==============

interface ChildEntitySectionProps {
  entityDef: string
  displayName: string
  attributes: EntityAttribute[]
  isExpanded: boolean
  onToggle: () => void
  onFieldDragStart: (attr: EntityAttribute) => void
  onFieldDragEnd: () => void
  onFieldDoubleClick: (attr: EntityAttribute) => void
  canAddToSection: boolean
}

function ChildEntitySection({
  entityDef, displayName, attributes, isExpanded, onToggle,
  onFieldDragStart, onFieldDragEnd, onFieldDoubleClick, canAddToSection
}: ChildEntitySectionProps) {
  return (
    <div className={`child-entity-section ${isExpanded ? 'expanded' : ''}`}>
      <button className="child-entity-header" onClick={onToggle}>
        <span className="child-entity-chevron">
          {isExpanded ? <FolderOpen size={16} /> : <Folder size={16} />}
        </span>
        <span className="child-entity-title">{displayName}</span>
        <span className="child-entity-count">{attributes.length} fields</span>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="child-entity-content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {attributes.map((field) => (
              <FieldItem
                key={field.path}
                attribute={field}
                onDragStart={() => onFieldDragStart(field)}
                onDragEnd={onFieldDragEnd}
                onDoubleClick={() => onFieldDoubleClick(field)}
                canAdd={canAddToSection}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ============== Main Field Palette ==============

export function FieldPalette() {
  const { state, dispatch, actions } = useBuilder()
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['common', 'dates']))
  const [expandedChildren, setExpandedChildren] = useState<Set<string>>(new Set())

  // Group fields by type/category
  const groupedFields = useMemo(() => {
    if (!state.entitySchema) return null

    const attrs = state.entitySchema.attributes
    const filtered = searchTerm
      ? attrs.filter(a =>
          a.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          a.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (a.label && a.label.toLowerCase().includes(searchTerm.toLowerCase()))
        )
      : attrs

    // Group by format type
    const groups: Record<string, EntityAttribute[]> = {
      common: [],
      dates: [],
      numbers: [],
      text: [],
      other: [],
    }

    filtered.forEach(attr => {
      // Common fields (typically shown at top)
      if (['Number', 'Name', 'Description', 'Status', 'Id'].some(k => attr.path.includes(k))) {
        groups.common.push(attr)
      } else if (['date', 'datetime'].includes(attr.format)) {
        groups.dates.push(attr)
      } else if (['number', 'currency', 'percent'].includes(attr.format)) {
        groups.numbers.push(attr)
      } else if (['text', 'rich_text'].includes(attr.format)) {
        groups.text.push(attr)
      } else {
        groups.other.push(attr)
      }
    })

    return groups
  }, [state.entitySchema, searchTerm])

  const toggleGroup = useCallback((group: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev)
      if (next.has(group)) next.delete(group)
      else next.add(group)
      return next
    })
  }, [])

  const toggleChild = useCallback((path: string) => {
    setExpandedChildren(prev => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }, [])

  const handleFieldDragStart = useCallback((attr: EntityAttribute) => {
    dispatch({
      type: 'SET_DRAG_ITEM',
      payload: { type: 'new-field', data: attr }
    })
  }, [dispatch])

  const handleFieldDragEnd = useCallback(() => {
    dispatch({ type: 'SET_DRAG_ITEM', payload: null })
  }, [dispatch])

  const handleFieldDoubleClick = useCallback((attr: EntityAttribute) => {
    // Add field to currently selected section
    if (state.selection.type === 'section' && state.selection.id) {
      const section = state.template.sections.find(s => s.id === state.selection.id)
      if (section && (section.header_config || section.detail_config)) {
        const field: FieldMapping = {
          path: attr.path,
          label: attr.label || attr.name,
          format: attr.format,
        }
        actions.addField(state.selection.id, field)
      }
    }
  }, [state.selection, state.template.sections, actions])

  // Check if a section is selected that can accept fields
  const canAddToSection = useMemo(() => {
    if (state.selection.type !== 'section' || !state.selection.id) return false
    const section = state.template.sections.find(s => s.id === state.selection.id)
    return section ? !!(section.header_config || section.detail_config) : false
  }, [state.selection, state.template.sections])

  if (!state.entitySchema) {
    return (
      <div className="field-palette empty">
        <div className="empty-palette-content">
          <Database size={32} />
          <h4>No Entity Selected</h4>
          <p>Select a target entity to see available fields</p>
        </div>
      </div>
    )
  }

  return (
    <div className="field-palette">
      {/* Search */}
      <div className="palette-search">
        <Search size={14} />
        <input
          type="text"
          placeholder="Search fields..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Entity info */}
      <div className="palette-entity-info">
        <Database size={14} />
        <span className="entity-name">{state.entitySchema.display_name}</span>
      </div>

      {/* Field groups */}
      <div className="palette-groups">
        {groupedFields && (
          <>
            {groupedFields.common.length > 0 && (
              <FieldGroup
                title="Common Fields"
                icon={FileText}
                fields={groupedFields.common}
                isExpanded={expandedGroups.has('common')}
                onToggle={() => toggleGroup('common')}
                onFieldDragStart={handleFieldDragStart}
                onFieldDragEnd={handleFieldDragEnd}
                onFieldDoubleClick={handleFieldDoubleClick}
                canAddToSection={canAddToSection}
              />
            )}
            {groupedFields.dates.length > 0 && (
              <FieldGroup
                title="Dates"
                icon={Calendar}
                fields={groupedFields.dates}
                isExpanded={expandedGroups.has('dates')}
                onToggle={() => toggleGroup('dates')}
                onFieldDragStart={handleFieldDragStart}
                onFieldDragEnd={handleFieldDragEnd}
                onFieldDoubleClick={handleFieldDoubleClick}
                canAddToSection={canAddToSection}
              />
            )}
            {groupedFields.numbers.length > 0 && (
              <FieldGroup
                title="Numbers & Currency"
                icon={Hash}
                fields={groupedFields.numbers}
                isExpanded={expandedGroups.has('numbers')}
                onToggle={() => toggleGroup('numbers')}
                onFieldDragStart={handleFieldDragStart}
                onFieldDragEnd={handleFieldDragEnd}
                onFieldDoubleClick={handleFieldDoubleClick}
                canAddToSection={canAddToSection}
              />
            )}
            {groupedFields.text.length > 0 && (
              <FieldGroup
                title="Text Fields"
                icon={Type}
                fields={groupedFields.text}
                isExpanded={expandedGroups.has('text')}
                onToggle={() => toggleGroup('text')}
                onFieldDragStart={handleFieldDragStart}
                onFieldDragEnd={handleFieldDragEnd}
                onFieldDoubleClick={handleFieldDoubleClick}
                canAddToSection={canAddToSection}
              />
            )}
            {groupedFields.other.length > 0 && (
              <FieldGroup
                title="Other"
                icon={List}
                fields={groupedFields.other}
                isExpanded={expandedGroups.has('other')}
                onToggle={() => toggleGroup('other')}
                onFieldDragStart={handleFieldDragStart}
                onFieldDragEnd={handleFieldDragEnd}
                onFieldDoubleClick={handleFieldDoubleClick}
                canAddToSection={canAddToSection}
              />
            )}
          </>
        )}

        {/* Child entities */}
        {state.entitySchema.child_entities.length > 0 && (
          <div className="child-entities-section">
            <div className="child-entities-header">
              <List size={14} />
              <span>Child Collections</span>
            </div>
            {state.entitySchema.child_entities.map(child => (
              <ChildEntitySection
                key={child.path}
                entityDef={child.entity_def}
                displayName={child.display_name}
                attributes={child.attributes}
                isExpanded={expandedChildren.has(child.path)}
                onToggle={() => toggleChild(child.path)}
                onFieldDragStart={handleFieldDragStart}
                onFieldDragEnd={handleFieldDragEnd}
                onFieldDoubleClick={handleFieldDoubleClick}
                canAddToSection={canAddToSection}
              />
            ))}
          </div>
        )}
      </div>

      {/* Contextual hint */}
      <div className={`palette-hint ${canAddToSection ? 'has-selection' : ''}`}>
        <span>
          {canAddToSection 
            ? 'Click + or drag fields to add to selected section'
            : state.template.sections.length === 0
              ? 'Add a section first, then add fields to it'
              : 'Select a Header or Detail section to add fields'
          }
        </span>
      </div>
    </div>
  )
}

export default FieldPalette
