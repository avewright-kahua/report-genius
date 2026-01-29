/**
 * Template Preview Pane
 * 
 * Real-time preview of the template with sample data
 */

import React, { useState, useMemo, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Eye, Maximize2, Minimize2, RefreshCw, Download, FileText, Loader2,
  AlertCircle, Database, ChevronLeft, ChevronRight
} from 'lucide-react'
import { useBuilder } from './BuilderState'
import { PortableTemplate, Section, FieldMapping, FieldFormat } from './types'

// ============== Format Helpers ==============

function formatValue(value: any, format: FieldFormat): string {
  if (value === null || value === undefined) return '—'

  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(Number(value) || 0)

    case 'number':
      return new Intl.NumberFormat('en-US').format(Number(value) || 0)

    case 'percent':
      return `${(Number(value) * 100).toFixed(1)}%`

    case 'date':
      try {
        return new Date(value).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        })
      } catch {
        return String(value)
      }

    case 'datetime':
      try {
        return new Date(value).toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch {
        return String(value)
      }

    case 'boolean':
      return value ? 'Yes' : 'No'

    default:
      return String(value)
  }
}

function getValueFromPath(data: Record<string, any>, path: string): any {
  if (!data || !path) return undefined

  const parts = path.split('.')
  let current: any = data

  for (const part of parts) {
    if (current === null || current === undefined) return undefined
    current = current[part]
  }

  return current
}

function interpolateTemplate(template: string, data: Record<string, any>): string {
  return template.replace(/\{([^}]+)\}/g, (match, path) => {
    const value = getValueFromPath(data, path)
    return value !== undefined ? String(value) : match
  })
}

// ============== Preview Section Components ==============

function PreviewHeader({ section, data, style }: {
  section: Section
  data: Record<string, any>
  style: PortableTemplate['style']
}) {
  const config = section.header_config!

  return (
    <div className="preview-section preview-header" style={{ backgroundColor: style.primary_color + '10' }}>
      {config.title_template && (
        <h2 className="preview-title" style={{ color: style.primary_color }}>
          {interpolateTemplate(config.title_template, data)}
        </h2>
      )}
      <div className={`preview-fields-grid layout-${config.layout} cols-${config.columns}`}>
        {config.fields.map((field, i) => {
          const value = getValueFromPath(data, field.path)
          return (
            <div key={i} className="preview-field">
              {config.show_labels && (
                <span className="preview-label">{field.label || field.path}:</span>
              )}
              <span className="preview-value">{formatValue(value, field.format)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function PreviewDetail({ section, data }: {
  section: Section
  data: Record<string, any>
}) {
  const config = section.detail_config!

  return (
    <div className="preview-section preview-detail">
      {section.title && <h3 className="preview-section-title">{section.title}</h3>}
      <div className={`preview-fields-grid layout-${config.layout} cols-${config.columns}`}>
        {config.fields.map((field, i) => {
          const value = getValueFromPath(data, field.path)
          return (
            <div key={i} className="preview-field">
              {config.show_labels && (
                <span className="preview-label">{field.label || field.path}:</span>
              )}
              <span className="preview-value">{formatValue(value, field.format)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function PreviewTable({ section, data, style }: {
  section: Section
  data: Record<string, any>
  style: PortableTemplate['style']
}) {
  const config = section.table_config!
  const items = getValueFromPath(data, config.source) || []

  return (
    <div className="preview-section preview-table">
      {section.title && <h3 className="preview-section-title">{section.title}</h3>}
      <table className="preview-data-table">
        {config.show_header && (
          <thead style={{ backgroundColor: style.table_header_bg, color: style.table_header_fg }}>
            <tr>
              {config.show_row_numbers && <th style={{ width: 40 }}>#</th>}
              {config.columns.map((col, i) => (
                <th
                  key={i}
                  style={{ textAlign: col.alignment, width: col.width ? `${col.width}%` : undefined }}
                >
                  {col.field.label || col.field.path}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td colSpan={config.columns.length + (config.show_row_numbers ? 1 : 0)} className="empty-message">
                {config.empty_message}
              </td>
            </tr>
          ) : (
            items.slice(0, 10).map((item: any, rowIndex: number) => (
              <tr
                key={rowIndex}
                style={{
                  backgroundColor: rowIndex % 2 === 1 ? style.table_alt_row_bg : undefined
                }}
              >
                {config.show_row_numbers && <td className="row-number">{rowIndex + 1}</td>}
                {config.columns.map((col, colIndex) => {
                  const value = getValueFromPath(item, col.field.path)
                  return (
                    <td key={colIndex} style={{ textAlign: col.alignment }}>
                      {formatValue(value, col.field.format)}
                    </td>
                  )
                })}
              </tr>
            ))
          )}
          {items.length > 10 && (
            <tr className="more-rows">
              <td colSpan={config.columns.length + (config.show_row_numbers ? 1 : 0)}>
                ... and {items.length - 10} more rows
              </td>
            </tr>
          )}
        </tbody>
        {config.show_subtotals && config.subtotal_fields.length > 0 && items.length > 0 && (
          <tfoot style={{ borderTop: `2px solid ${style.table_border_color}` }}>
            <tr>
              {config.show_row_numbers && <td />}
              {config.columns.map((col, i) => {
                const isSubtotal = config.subtotal_fields.includes(col.field.path)
                if (!isSubtotal) return <td key={i} />

                const total = items.reduce((sum: number, item: any) => {
                  const val = getValueFromPath(item, col.field.path)
                  return sum + (Number(val) || 0)
                }, 0)

                return (
                  <td key={i} style={{ textAlign: col.alignment, fontWeight: 'bold' }}>
                    {formatValue(total, col.field.format)}
                  </td>
                )
              })}
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  )
}

function PreviewText({ section, data }: {
  section: Section
  data: Record<string, any>
}) {
  const config = section.text_config!

  return (
    <div className="preview-section preview-text">
      {section.title && <h3 className="preview-section-title">{section.title}</h3>}
      <div className="preview-text-content">
        {interpolateTemplate(config.content, data)}
      </div>
    </div>
  )
}

function PreviewPageBreak() {
  return (
    <div className="preview-section preview-page-break">
      <div className="page-break-indicator">
        <span>— Page Break —</span>
      </div>
    </div>
  )
}

// ============== Sample Data Generator ==============

function generateSampleData(template: PortableTemplate): Record<string, any> {
  // Generate realistic sample data based on template fields
  const data: Record<string, any> = {
    Id: 12345,
    Number: 'CTR-2024-001',
    Name: 'Sample Contract',
    Description: 'Professional Services Agreement for Project Implementation',
    Status: { Name: 'Active', Id: 1 },
    Date: new Date().toISOString(),
    CreatedDateTime: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    ScheduleStart: new Date().toISOString(),
    ScheduleEnd: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString(),
    ContractorCompany: { ShortLabel: 'ABC Construction LLC', Name: 'ABC Construction LLC' },
    ClientCompany: { ShortLabel: 'Client Corp', Name: 'Client Corporation' },
    Author: { ShortLabel: 'John Smith', Name: 'John Smith' },
    AssignedTo: { ShortLabel: 'Jane Doe', Name: 'Jane Doe' },
    OriginalContractAmount: 1250000,
    CurrentContractAmount: 1375000,
    TotalValue: 1375000,
    Amount: 1375000,
    Type: 'Fixed Price',
    ScopeOfWork: 'Complete renovation of building A including electrical, plumbing, and HVAC upgrades.',
    Notes: 'Contract includes 10% contingency for unforeseen conditions.',
    DomainPartition: { Name: 'Main Office Renovation', Number: 'PRJ-001' },
    
    // Sample child items
    Items: [
      { Number: '001', Description: 'Electrical Work', TotalValue: 250000, Status: 'Complete' },
      { Number: '002', Description: 'Plumbing Installation', TotalValue: 185000, Status: 'In Progress' },
      { Number: '003', Description: 'HVAC System', TotalValue: 425000, Status: 'Pending' },
      { Number: '004', Description: 'General Construction', TotalValue: 350000, Status: 'In Progress' },
      { Number: '005', Description: 'Finishing Work', TotalValue: 165000, Status: 'Not Started' },
    ],
    References: [
      { Type: 'RFI', Number: 'RFI-001', Subject: 'Clarification on electrical layout' },
      { Type: 'Submittal', Number: 'SUB-001', Subject: 'HVAC equipment specifications' },
    ],
  }

  return data
}

// ============== Main Preview Component ==============

export function TemplatePreview() {
  const { state, dispatch } = useBuilder()
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [zoom, setZoom] = useState(100)

  // Generate or use provided sample data
  const previewData = useMemo(() => {
    return state.previewData || generateSampleData(state.template)
  }, [state.previewData, state.template])

  // Load real sample data from API
  const loadSampleData = useCallback(async () => {
    if (!state.template.target_entity_def) return

    setIsLoading(true)
    try {
      const response = await fetch('/api/template/sample-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity_def: state.template.target_entity_def }),
      })

      if (response.ok) {
        const data = await response.json()
        dispatch({ type: 'SET_PREVIEW_DATA', payload: data })
      }
    } catch (error) {
      console.error('Failed to load sample data:', error)
    } finally {
      setIsLoading(false)
    }
  }, [state.template.target_entity_def, dispatch])

  const handleDownload = useCallback(async () => {
    // Trigger document generation
    setIsLoading(true)
    try {
      const response = await fetch('/api/template/render-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template: state.template,
          data: previewData,
        }),
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${state.template.name || 'template'}-preview.docx`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Failed to generate preview:', error)
    } finally {
      setIsLoading(false)
    }
  }, [state.template, previewData])

  const pageStyle = {
    transform: `scale(${zoom / 100})`,
    transformOrigin: 'top center',
  }

  return (
    <div className={`template-preview ${isFullscreen ? 'fullscreen' : ''}`}>
      {/* Toolbar */}
      <div className="preview-toolbar">
        <div className="preview-title">
          <Eye size={16} />
          <span>Preview</span>
        </div>

        <div className="preview-actions">
          <button
            className="preview-action-btn"
            onClick={loadSampleData}
            disabled={isLoading || !state.template.target_entity_def}
            title="Load real sample data"
          >
            <Database size={14} />
          </button>

          <div className="zoom-controls">
            <button onClick={() => setZoom(z => Math.max(50, z - 10))}>
              <Minimize2 size={14} />
            </button>
            <span>{zoom}%</span>
            <button onClick={() => setZoom(z => Math.min(150, z + 10))}>
              <Maximize2 size={14} />
            </button>
          </div>

          <button
            className="preview-action-btn"
            onClick={handleDownload}
            disabled={isLoading}
            title="Download preview"
          >
            {isLoading ? <Loader2 size={14} className="spin" /> : <Download size={14} />}
          </button>

          <button
            className="preview-action-btn"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
        </div>
      </div>

      {/* Preview content */}
      <div className="preview-container">
        {state.template.sections.length === 0 ? (
          <div className="preview-empty">
            <FileText size={48} />
            <h4>No sections yet</h4>
            <p>Add sections to see a preview of your template</p>
          </div>
        ) : (
          <div
            className={`preview-page ${state.template.layout.orientation}`}
            style={pageStyle}
          >
            {/* Page content */}
            <div
              className="preview-page-content"
              style={{
                paddingTop: `${state.template.layout.margin_top * 72}px`,
                paddingBottom: `${state.template.layout.margin_bottom * 72}px`,
                paddingLeft: `${state.template.layout.margin_left * 72}px`,
                paddingRight: `${state.template.layout.margin_right * 72}px`,
              }}
            >
              {state.template.sections
                .sort((a, b) => a.order - b.order)
                .map((section) => {
                  switch (section.type) {
                    case 'header':
                      return section.header_config && (
                        <PreviewHeader
                          key={section.id}
                          section={section}
                          data={previewData}
                          style={state.template.style}
                        />
                      )
                    case 'detail':
                      return section.detail_config && (
                        <PreviewDetail
                          key={section.id}
                          section={section}
                          data={previewData}
                        />
                      )
                    case 'table':
                      return section.table_config && (
                        <PreviewTable
                          key={section.id}
                          section={section}
                          data={previewData}
                          style={state.template.style}
                        />
                      )
                    case 'text':
                      return section.text_config && (
                        <PreviewText
                          key={section.id}
                          section={section}
                          data={previewData}
                        />
                      )
                    case 'page_break':
                      return <PreviewPageBreak key={section.id} />
                    default:
                      return (
                        <div key={section.id} className="preview-section preview-placeholder">
                          {section.type} section
                        </div>
                      )
                  }
                })}
            </div>
          </div>
        )}
      </div>

      {/* Data info */}
      <div className="preview-data-info">
        <span>Showing sample data</span>
        <button onClick={() => dispatch({ type: 'SET_PREVIEW_DATA', payload: null })}>
          <RefreshCw size={12} />
          Reset
        </button>
      </div>
    </div>
  )
}

export default TemplatePreview
