/**
 * Template Builder State Management
 * 
 * Reducer and context for the visual template editor
 */

import React, { createContext, useContext, useReducer, useCallback, useRef, useMemo } from 'react'
import {
  BuilderState,
  BuilderAction,
  PortableTemplate,
  Section,
  FieldMapping,
  ColumnDef,
  Selection,
  DEFAULT_TEMPLATE,
  DEFAULT_PAGE_LAYOUT,
  DEFAULT_STYLE_CONFIG,
} from './types'

// Generate unique IDs
const genId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`

// ============== Initial State ==============

const initialState: BuilderState = {
  template: DEFAULT_TEMPLATE,
  originalTemplate: undefined,
  entitySchema: null,
  availableEntities: [],
  mode: 'design',
  selection: { type: null, id: null },
  hoveredId: null,
  dragItem: null,
  dropTarget: null,
  history: { past: [], future: [] },
  isDirty: false,
  leftPanelWidth: 280,
  rightPanelWidth: 320,
  expandedPanels: new Set(['sections', 'fields', 'properties']),
  ai: {
    isOpen: false,
    isLoading: false,
    suggestions: [],
    conversation: [],
  },
  previewData: null,
  isLoading: false,
  isSaving: false,
}

// ============== Helper Functions ==============

function updateSectionFields(section: Section, updater: (fields: FieldMapping[]) => FieldMapping[]): Section {
  if (section.header_config) {
    return {
      ...section,
      header_config: {
        ...section.header_config,
        fields: updater(section.header_config.fields),
      },
    }
  }
  if (section.detail_config) {
    return {
      ...section,
      detail_config: {
        ...section.detail_config,
        fields: updater(section.detail_config.fields),
      },
    }
  }
  return section
}

function updateSectionColumns(section: Section, updater: (columns: ColumnDef[]) => ColumnDef[]): Section {
  if (section.table_config) {
    return {
      ...section,
      table_config: {
        ...section.table_config,
        columns: updater(section.table_config.columns),
      },
    }
  }
  return section
}

function reorderArray<T>(arr: T[], fromIndex: number, toIndex: number): T[] {
  const result = [...arr]
  const [removed] = result.splice(fromIndex, 1)
  result.splice(toIndex, 0, removed)
  return result
}

// ============== Reducer ==============

function builderReducer(state: BuilderState, action: BuilderAction): BuilderState {
  switch (action.type) {
    // Template operations
    case 'SET_TEMPLATE':
      return {
        ...state,
        template: action.payload,
        originalTemplate: action.payload,
        isDirty: false,
        history: { past: [], future: [] },
      }

    case 'UPDATE_TEMPLATE_METADATA':
      return {
        ...state,
        template: { ...state.template, ...action.payload },
        isDirty: true,
      }

    case 'UPDATE_LAYOUT':
      return {
        ...state,
        template: {
          ...state.template,
          layout: { ...state.template.layout, ...action.payload },
        },
        isDirty: true,
      }

    case 'UPDATE_STYLE':
      return {
        ...state,
        template: {
          ...state.template,
          style: { ...state.template.style, ...action.payload },
        },
        isDirty: true,
      }

    // Section operations
    case 'ADD_SECTION': {
      const { section, afterId } = action.payload
      const newSection = { ...section, id: section.id || genId() }
      let sections = [...state.template.sections]
      
      if (afterId) {
        const idx = sections.findIndex(s => s.id === afterId)
        if (idx >= 0) {
          sections.splice(idx + 1, 0, newSection)
        } else {
          sections.push(newSection)
        }
      } else {
        sections.push(newSection)
      }
      
      // Recompute order
      sections = sections.map((s, i) => ({ ...s, order: i }))
      
      return {
        ...state,
        template: { ...state.template, sections },
        selection: { type: 'section', id: newSection.id },
        isDirty: true,
      }
    }

    case 'UPDATE_SECTION': {
      const { id, updates } = action.payload
      const sections = state.template.sections.map(s =>
        s.id === id ? { ...s, ...updates } : s
      )
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    case 'DELETE_SECTION': {
      const sections = state.template.sections
        .filter(s => s.id !== action.payload)
        .map((s, i) => ({ ...s, order: i }))
      return {
        ...state,
        template: { ...state.template, sections },
        selection: state.selection.id === action.payload
          ? { type: null, id: null }
          : state.selection,
        isDirty: true,
      }
    }

    case 'MOVE_SECTION': {
      const { id, newIndex } = action.payload
      const currentIndex = state.template.sections.findIndex(s => s.id === id)
      if (currentIndex < 0) return state
      
      const sections = reorderArray(state.template.sections, currentIndex, newIndex)
        .map((s, i) => ({ ...s, order: i }))
      
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    case 'DUPLICATE_SECTION': {
      const original = state.template.sections.find(s => s.id === action.payload)
      if (!original) return state
      
      const duplicate: Section = {
        ...JSON.parse(JSON.stringify(original)),
        id: genId(),
        title: original.title ? `${original.title} (Copy)` : undefined,
      }
      
      const idx = state.template.sections.findIndex(s => s.id === action.payload)
      const sections = [...state.template.sections]
      sections.splice(idx + 1, 0, duplicate)
      
      return {
        ...state,
        template: {
          ...state.template,
          sections: sections.map((s, i) => ({ ...s, order: i })),
        },
        selection: { type: 'section', id: duplicate.id },
        isDirty: true,
      }
    }

    // Field operations
    case 'ADD_FIELD': {
      const { sectionId, field } = action.payload
      const sections = state.template.sections.map(s => {
        if (s.id !== sectionId) return s
        return updateSectionFields(s, fields => [...fields, field])
      })
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    case 'UPDATE_FIELD': {
      const { sectionId, fieldIndex, updates } = action.payload
      const sections = state.template.sections.map(s => {
        if (s.id !== sectionId) return s
        return updateSectionFields(s, fields =>
          fields.map((f, i) => i === fieldIndex ? { ...f, ...updates } : f)
        )
      })
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    case 'DELETE_FIELD': {
      const { sectionId, fieldIndex } = action.payload
      const sections = state.template.sections.map(s => {
        if (s.id !== sectionId) return s
        return updateSectionFields(s, fields => fields.filter((_, i) => i !== fieldIndex))
      })
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    case 'MOVE_FIELD': {
      const { sectionId, fromIndex, toIndex } = action.payload
      const sections = state.template.sections.map(s => {
        if (s.id !== sectionId) return s
        return updateSectionFields(s, fields => reorderArray(fields, fromIndex, toIndex))
      })
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    // Column operations
    case 'ADD_COLUMN': {
      const { sectionId, column } = action.payload
      const newColumn = { ...column, id: column.id || genId() }
      const sections = state.template.sections.map(s => {
        if (s.id !== sectionId) return s
        return updateSectionColumns(s, columns => [...columns, newColumn])
      })
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    case 'UPDATE_COLUMN': {
      const { sectionId, columnId, updates } = action.payload
      const sections = state.template.sections.map(s => {
        if (s.id !== sectionId) return s
        return updateSectionColumns(s, columns =>
          columns.map(c => c.id === columnId ? { ...c, ...updates } : c)
        )
      })
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    case 'DELETE_COLUMN': {
      const { sectionId, columnId } = action.payload
      const sections = state.template.sections.map(s => {
        if (s.id !== sectionId) return s
        return updateSectionColumns(s, columns => columns.filter(c => c.id !== columnId))
      })
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    case 'MOVE_COLUMN': {
      const { sectionId, fromIndex, toIndex } = action.payload
      const sections = state.template.sections.map(s => {
        if (s.id !== sectionId) return s
        return updateSectionColumns(s, columns => reorderArray(columns, fromIndex, toIndex))
      })
      return {
        ...state,
        template: { ...state.template, sections },
        isDirty: true,
      }
    }

    // UI state
    case 'SET_MODE':
      return { ...state, mode: action.payload }

    case 'SET_SELECTION':
      return { ...state, selection: action.payload }

    case 'SET_HOVERED':
      return { ...state, hoveredId: action.payload }

    case 'SET_DRAG_ITEM':
      return { ...state, dragItem: action.payload }

    case 'SET_DROP_TARGET':
      return { ...state, dropTarget: action.payload }

    case 'TOGGLE_PANEL': {
      const expandedPanels = new Set(state.expandedPanels)
      if (expandedPanels.has(action.payload)) {
        expandedPanels.delete(action.payload)
      } else {
        expandedPanels.add(action.payload)
      }
      return { ...state, expandedPanels }
    }

    case 'SET_PANEL_WIDTH':
      return {
        ...state,
        [action.payload.panel === 'left' ? 'leftPanelWidth' : 'rightPanelWidth']: action.payload.width,
      }

    // Entity schema
    case 'SET_ENTITY_SCHEMA':
      return { ...state, entitySchema: action.payload }

    case 'SET_AVAILABLE_ENTITIES':
      return { ...state, availableEntities: action.payload }

    // History
    case 'SAVE_SNAPSHOT':
      return {
        ...state,
        history: {
          past: [...state.history.past.slice(-50), state.template],
          future: [],
        },
      }

    case 'UNDO': {
      if (state.history.past.length === 0) return state
      const previous = state.history.past[state.history.past.length - 1]
      return {
        ...state,
        template: previous,
        history: {
          past: state.history.past.slice(0, -1),
          future: [state.template, ...state.history.future],
        },
      }
    }

    case 'REDO': {
      if (state.history.future.length === 0) return state
      const next = state.history.future[0]
      return {
        ...state,
        template: next,
        history: {
          past: [...state.history.past, state.template],
          future: state.history.future.slice(1),
        },
      }
    }

    case 'MARK_CLEAN':
      return {
        ...state,
        isDirty: false,
        originalTemplate: state.template,
      }

    // AI Assistant
    case 'TOGGLE_AI':
      return {
        ...state,
        ai: {
          ...state.ai,
          isOpen: action.payload ?? !state.ai.isOpen,
        },
      }

    case 'SET_AI_LOADING':
      return { ...state, ai: { ...state.ai, isLoading: action.payload } }

    case 'ADD_AI_MESSAGE':
      return {
        ...state,
        ai: {
          ...state.ai,
          conversation: [...state.ai.conversation, action.payload],
        },
      }

    case 'SET_AI_SUGGESTIONS':
      return { ...state, ai: { ...state.ai, suggestions: action.payload } }

    case 'APPLY_AI_TEMPLATE':
      return {
        ...state,
        template: action.payload,
        isDirty: true,
        history: {
          past: [...state.history.past, state.template],
          future: [],
        },
      }

    // Preview
    case 'SET_PREVIEW_DATA':
      return { ...state, previewData: action.payload, previewError: undefined }

    case 'SET_PREVIEW_ERROR':
      return { ...state, previewError: action.payload }

    // Loading
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }

    case 'SET_SAVING':
      return { ...state, isSaving: action.payload }

    case 'SET_ERROR':
      return { ...state, error: action.payload }

    default:
      return state
  }
}

// ============== Context ==============

interface BuilderContextValue {
  state: BuilderState
  dispatch: React.Dispatch<BuilderAction>
  
  // Convenience actions
  actions: {
    setTemplate: (template: PortableTemplate) => void
    updateMetadata: (updates: Partial<PortableTemplate>) => void
    addSection: (section: Section, afterId?: string) => void
    updateSection: (id: string, updates: Partial<Section>) => void
    deleteSection: (id: string) => void
    moveSection: (id: string, newIndex: number) => void
    duplicateSection: (id: string) => void
    addField: (sectionId: string, field: FieldMapping) => void
    updateField: (sectionId: string, fieldIndex: number, updates: Partial<FieldMapping>) => void
    deleteField: (sectionId: string, fieldIndex: number) => void
    moveField: (sectionId: string, fromIndex: number, toIndex: number) => void
    addColumn: (sectionId: string, column: ColumnDef) => void
    updateColumn: (sectionId: string, columnId: string, updates: Partial<ColumnDef>) => void
    deleteColumn: (sectionId: string, columnId: string) => void
    moveColumn: (sectionId: string, fromIndex: number, toIndex: number) => void
    select: (selection: Selection) => void
    clearSelection: () => void
    undo: () => void
    redo: () => void
    saveSnapshot: () => void
  }
}

const BuilderContext = createContext<BuilderContextValue | null>(null)

export function BuilderProvider({ children, initialTemplate }: { 
  children: React.ReactNode
  initialTemplate?: PortableTemplate 
}) {
  const [state, dispatch] = useReducer(builderReducer, {
    ...initialState,
    template: initialTemplate || DEFAULT_TEMPLATE,
    originalTemplate: initialTemplate,
  })

  const actions = useMemo(() => ({
    setTemplate: (template: PortableTemplate) => 
      dispatch({ type: 'SET_TEMPLATE', payload: template }),
    
    updateMetadata: (updates: Partial<PortableTemplate>) =>
      dispatch({ type: 'UPDATE_TEMPLATE_METADATA', payload: updates }),
    
    addSection: (section: Section, afterId?: string) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'ADD_SECTION', payload: { section, afterId } })
    },
    
    updateSection: (id: string, updates: Partial<Section>) =>
      dispatch({ type: 'UPDATE_SECTION', payload: { id, updates } }),
    
    deleteSection: (id: string) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'DELETE_SECTION', payload: id })
    },
    
    moveSection: (id: string, newIndex: number) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'MOVE_SECTION', payload: { id, newIndex } })
    },
    
    duplicateSection: (id: string) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'DUPLICATE_SECTION', payload: id })
    },
    
    addField: (sectionId: string, field: FieldMapping) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'ADD_FIELD', payload: { sectionId, field } })
    },
    
    updateField: (sectionId: string, fieldIndex: number, updates: Partial<FieldMapping>) =>
      dispatch({ type: 'UPDATE_FIELD', payload: { sectionId, fieldIndex, updates } }),
    
    deleteField: (sectionId: string, fieldIndex: number) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'DELETE_FIELD', payload: { sectionId, fieldIndex } })
    },
    
    moveField: (sectionId: string, fromIndex: number, toIndex: number) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'MOVE_FIELD', payload: { sectionId, fromIndex, toIndex } })
    },
    
    addColumn: (sectionId: string, column: ColumnDef) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'ADD_COLUMN', payload: { sectionId, column } })
    },
    
    updateColumn: (sectionId: string, columnId: string, updates: Partial<ColumnDef>) =>
      dispatch({ type: 'UPDATE_COLUMN', payload: { sectionId, columnId, updates } }),
    
    deleteColumn: (sectionId: string, columnId: string) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'DELETE_COLUMN', payload: { sectionId, columnId } })
    },
    
    moveColumn: (sectionId: string, fromIndex: number, toIndex: number) => {
      dispatch({ type: 'SAVE_SNAPSHOT' })
      dispatch({ type: 'MOVE_COLUMN', payload: { sectionId, fromIndex, toIndex } })
    },
    
    select: (selection: Selection) =>
      dispatch({ type: 'SET_SELECTION', payload: selection }),
    
    clearSelection: () =>
      dispatch({ type: 'SET_SELECTION', payload: { type: null, id: null } }),
    
    undo: () => dispatch({ type: 'UNDO' }),
    redo: () => dispatch({ type: 'REDO' }),
    saveSnapshot: () => dispatch({ type: 'SAVE_SNAPSHOT' }),
  }), [dispatch])

  const value = useMemo(() => ({ state, dispatch, actions }), [state, actions])

  return (
    <BuilderContext.Provider value={value}>
      {children}
    </BuilderContext.Provider>
  )
}

export function useBuilder() {
  const context = useContext(BuilderContext)
  if (!context) {
    throw new Error('useBuilder must be used within a BuilderProvider')
  }
  return context
}

export function useBuilderState() {
  return useBuilder().state
}

export function useBuilderActions() {
  return useBuilder().actions
}

// ============== Keyboard Shortcuts Hook ==============

export function useBuilderKeyboard() {
  const { state, dispatch, actions } = useBuilder()

  React.useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return
      }

      // Undo/Redo
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault()
        if (e.shiftKey) {
          actions.redo()
        } else {
          actions.undo()
        }
        return
      }

      // Delete
      if ((e.key === 'Delete' || e.key === 'Backspace') && state.selection.id) {
        e.preventDefault()
        if (state.selection.type === 'section') {
          actions.deleteSection(state.selection.id)
        }
        return
      }

      // Escape - clear selection
      if (e.key === 'Escape') {
        actions.clearSelection()
        return
      }

      // D - Duplicate
      if (e.key === 'd' && (e.metaKey || e.ctrlKey) && state.selection.type === 'section') {
        e.preventDefault()
        actions.duplicateSection(state.selection.id!)
        return
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [state.selection, actions])
}
