/**
 * Portable View Template Builder Types
 * 
 * State management and type definitions for the visual template editor
 */

// ============== Core Schema Types (mirror Python schema) ==============

export type FieldFormat = 
  | 'text' | 'number' | 'currency' | 'date' | 'datetime' 
  | 'percent' | 'boolean' | 'rich_text' | 'image' | 'url'

export type SectionType = 
  | 'header' | 'detail' | 'table' | 'text' | 'image' 
  | 'chart' | 'signature' | 'footer' | 'page_break' | 'grouped_table'

export type Alignment = 'left' | 'center' | 'right'
export type LayoutMode = 'horizontal' | 'vertical' | 'grid'
export type Orientation = 'portrait' | 'landscape'

export interface FieldMapping {
  path: string           // Dot-notation: "Status.Name", "Items[0].Amount"
  label?: string         // Display label
  format: FieldFormat
  format_options?: Record<string, any>
  default_value?: string
  condition?: Record<string, any>
  transform?: string
}

export interface ColumnDef {
  id: string              // Unique ID for drag-drop
  field: FieldMapping
  width?: number          // Percentage or inches
  alignment: Alignment
  header_style?: Record<string, any>
  cell_style?: Record<string, any>
}

export interface TableConfig {
  source: string          // Path to child collection
  entity_def?: string
  columns: ColumnDef[]
  show_header: boolean
  show_row_numbers: boolean
  sort_by?: string
  sort_direction: 'asc' | 'desc'
  filter_condition?: Record<string, any>
  group_by?: string
  show_subtotals: boolean
  subtotal_fields: string[]
  max_rows?: number
  empty_message: string
}

export interface HeaderConfig {
  fields: FieldMapping[]
  layout: LayoutMode
  columns: number
  show_labels: boolean
  title_template?: string
}

export interface DetailConfig {
  fields: FieldMapping[]
  layout: LayoutMode
  columns: number
  show_labels: boolean
  label_width?: number
}

export interface TextConfig {
  content: string
  style?: Record<string, any>
}

export interface ChartConfig {
  chart_type: 'bar' | 'line' | 'pie' | 'horizontal_bar' | 'stacked_bar' | 'donut'
  title: string
  data_source: string
  label_field: string
  value_field: string
  series_field?: string
  colors?: string[]
  width: number
  height: number
  show_legend: boolean
  show_values: boolean
}

export interface Section {
  id: string              // Unique ID for drag-drop
  type: SectionType
  title?: string
  order: number
  condition?: Record<string, any>
  
  // Type-specific configs
  header_config?: HeaderConfig
  detail_config?: DetailConfig
  table_config?: TableConfig
  text_config?: TextConfig
  chart_config?: ChartConfig
  
  // Styling
  background_color?: string
  border?: Record<string, any>
  padding?: { top: number; right: number; bottom: number; left: number }
  margin?: { top: number; right: number; bottom: number; left: number }
}

export interface PageLayout {
  orientation: Orientation
  margin_top: number
  margin_bottom: number
  margin_left: number
  margin_right: number
  header_height: number
  footer_height: number
}

export interface StyleConfig {
  primary_color: string
  secondary_color: string
  accent_color: string
  font_family: string
  heading_font: string
  title_size: number
  heading_size: number
  body_size: number
  table_header_bg: string
  table_header_fg: string
  table_alt_row_bg: string
  table_border_color: string
}

export interface PortableTemplate {
  id?: string
  name: string
  description?: string
  version: string
  target_entity_def: string
  target_entity_aliases: string[]
  layout: PageLayout
  style: StyleConfig
  sections: Section[]
  category: string
  tags: string[]
  is_public: boolean
  created_at?: string
  updated_at?: string
}

// ============== Entity Schema Types ==============

export interface EntityAttribute {
  path: string
  name: string
  label: string
  type: string            // Kahua type
  format: FieldFormat     // Mapped display format
  description?: string
  is_required?: boolean
  is_collection?: boolean
  child_entity_def?: string
}

export interface EntitySchema {
  entity_def: string
  display_name: string
  description?: string
  attributes: EntityAttribute[]
  child_entities: {
    path: string
    entity_def: string
    display_name: string
    attributes: EntityAttribute[]
  }[]
}

// ============== Builder State ==============

export type BuilderMode = 'design' | 'preview' | 'code'
export type SelectionType = 'section' | 'field' | 'column' | null

export interface Selection {
  type: SelectionType
  id: string | null
  sectionId?: string      // Parent section for field/column selection
}

export interface DragItem {
  type: 'section' | 'field' | 'column' | 'new-field' | 'new-section'
  id?: string
  data: any
}

export interface BuilderHistory {
  past: PortableTemplate[]
  future: PortableTemplate[]
}

export interface AIAssistant {
  isOpen: boolean
  isLoading: boolean
  lastSuggestion?: string
  suggestions: string[]
  conversation: {
    role: 'user' | 'assistant'
    content: string
  }[]
}

export interface BuilderState {
  // Core template
  template: PortableTemplate
  originalTemplate?: PortableTemplate  // For change detection
  
  // Entity context
  entitySchema: EntitySchema | null
  availableEntities: { entity_def: string; display_name: string }[]
  
  // UI state
  mode: BuilderMode
  selection: Selection
  hoveredId: string | null
  
  // Drag-drop
  dragItem: DragItem | null
  dropTarget: { id: string; position: 'before' | 'after' | 'inside' } | null
  
  // History (undo/redo)
  history: BuilderHistory
  isDirty: boolean
  
  // Panels
  leftPanelWidth: number
  rightPanelWidth: number
  expandedPanels: Set<string>
  
  // AI Assistant
  ai: AIAssistant
  
  // Preview
  previewData: Record<string, any> | null
  previewError?: string
  
  // Loading states
  isLoading: boolean
  isSaving: boolean
  error?: string
}

// ============== Actions ==============

export type BuilderAction =
  // Template operations
  | { type: 'SET_TEMPLATE'; payload: PortableTemplate }
  | { type: 'UPDATE_TEMPLATE_METADATA'; payload: Partial<PortableTemplate> }
  | { type: 'UPDATE_LAYOUT'; payload: Partial<PageLayout> }
  | { type: 'UPDATE_STYLE'; payload: Partial<StyleConfig> }
  
  // Section operations
  | { type: 'ADD_SECTION'; payload: { section: Section; afterId?: string } }
  | { type: 'UPDATE_SECTION'; payload: { id: string; updates: Partial<Section> } }
  | { type: 'DELETE_SECTION'; payload: string }
  | { type: 'MOVE_SECTION'; payload: { id: string; newIndex: number } }
  | { type: 'DUPLICATE_SECTION'; payload: string }
  
  // Field operations (for header/detail sections)
  | { type: 'ADD_FIELD'; payload: { sectionId: string; field: FieldMapping } }
  | { type: 'UPDATE_FIELD'; payload: { sectionId: string; fieldIndex: number; updates: Partial<FieldMapping> } }
  | { type: 'DELETE_FIELD'; payload: { sectionId: string; fieldIndex: number } }
  | { type: 'MOVE_FIELD'; payload: { sectionId: string; fromIndex: number; toIndex: number } }
  
  // Column operations (for table sections)
  | { type: 'ADD_COLUMN'; payload: { sectionId: string; column: ColumnDef } }
  | { type: 'UPDATE_COLUMN'; payload: { sectionId: string; columnId: string; updates: Partial<ColumnDef> } }
  | { type: 'DELETE_COLUMN'; payload: { sectionId: string; columnId: string } }
  | { type: 'MOVE_COLUMN'; payload: { sectionId: string; fromIndex: number; toIndex: number } }
  
  // UI state
  | { type: 'SET_MODE'; payload: BuilderMode }
  | { type: 'SET_SELECTION'; payload: Selection }
  | { type: 'SET_HOVERED'; payload: string | null }
  | { type: 'SET_DRAG_ITEM'; payload: DragItem | null }
  | { type: 'SET_DROP_TARGET'; payload: { id: string; position: 'before' | 'after' | 'inside' } | null }
  | { type: 'TOGGLE_PANEL'; payload: string }
  | { type: 'SET_PANEL_WIDTH'; payload: { panel: 'left' | 'right'; width: number } }
  
  // Entity schema
  | { type: 'SET_ENTITY_SCHEMA'; payload: EntitySchema }
  | { type: 'SET_AVAILABLE_ENTITIES'; payload: { entity_def: string; display_name: string }[] }
  
  // History
  | { type: 'UNDO' }
  | { type: 'REDO' }
  | { type: 'SAVE_SNAPSHOT' }
  | { type: 'MARK_CLEAN' }
  
  // AI Assistant
  | { type: 'TOGGLE_AI'; payload?: boolean }
  | { type: 'SET_AI_LOADING'; payload: boolean }
  | { type: 'ADD_AI_MESSAGE'; payload: { role: 'user' | 'assistant'; content: string } }
  | { type: 'SET_AI_SUGGESTIONS'; payload: string[] }
  | { type: 'APPLY_AI_TEMPLATE'; payload: PortableTemplate }
  
  // Preview
  | { type: 'SET_PREVIEW_DATA'; payload: Record<string, any> | null }
  | { type: 'SET_PREVIEW_ERROR'; payload: string }
  
  // Loading
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_SAVING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | undefined }

// ============== Utility Types ==============

export interface CreateSectionOptions {
  type: SectionType
  title?: string
  insertAfter?: string
}

export interface FieldDragData {
  attribute: EntityAttribute
  source: 'palette' | 'section'
  sourceSection?: string
  sourceIndex?: number
}

// Default values
export const DEFAULT_PAGE_LAYOUT: PageLayout = {
  orientation: 'portrait',
  margin_top: 1.0,
  margin_bottom: 1.0,
  margin_left: 1.0,
  margin_right: 1.0,
  header_height: 0.5,
  footer_height: 0.5,
}

export const DEFAULT_STYLE_CONFIG: StyleConfig = {
  primary_color: '#1a365d',
  secondary_color: '#3182ce',
  accent_color: '#38b2ac',
  font_family: 'Calibri',
  heading_font: 'Calibri',
  title_size: 24,
  heading_size: 14,
  body_size: 11,
  table_header_bg: '#1a365d',
  table_header_fg: '#ffffff',
  table_alt_row_bg: '#f7fafc',
  table_border_color: '#e2e8f0',
}

export const DEFAULT_TEMPLATE: PortableTemplate = {
  name: 'Untitled Template',
  version: '1.0',
  target_entity_def: '',
  target_entity_aliases: [],
  layout: DEFAULT_PAGE_LAYOUT,
  style: DEFAULT_STYLE_CONFIG,
  sections: [],
  category: 'custom',
  tags: [],
  is_public: false,
}

// Format display names
export const FORMAT_LABELS: Record<FieldFormat, string> = {
  text: 'Text',
  number: 'Number',
  currency: 'Currency',
  date: 'Date',
  datetime: 'Date & Time',
  percent: 'Percentage',
  boolean: 'Yes/No',
  rich_text: 'Rich Text',
  image: 'Image',
  url: 'Link',
}

export const SECTION_TYPE_LABELS: Record<SectionType, string> = {
  header: 'Header',
  detail: 'Details',
  table: 'Table',
  text: 'Text Block',
  image: 'Image',
  chart: 'Chart',
  signature: 'Signature',
  footer: 'Footer',
  page_break: 'Page Break',
  grouped_table: 'Grouped Table',
}

export const SECTION_TYPE_ICONS: Record<SectionType, string> = {
  header: 'FileText',
  detail: 'List',
  table: 'Table',
  text: 'AlignLeft',
  image: 'Image',
  chart: 'BarChart',
  signature: 'Edit3',
  footer: 'FileText',
  page_break: 'Minus',
  grouped_table: 'Layers',
}
