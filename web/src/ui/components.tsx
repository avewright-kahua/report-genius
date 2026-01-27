/**
 * Reusable UI Components for Kahua Assistant
 * SOTA patterns: compound components, render props, accessibility-first
 */

import React, { useState, useCallback, useEffect, useRef, memo, ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PieChart, Pie, Cell, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid
} from 'recharts'
import {
  TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle2,
  Clock, FileText, Download, ExternalLink, ChevronDown, ChevronUp,
  Sparkles, Zap, Database, Search as SearchIcon, Filter
} from 'lucide-react'

// ============== Color Palette ==============
export const CHART_COLORS = [
  '#10a37f', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444',
  '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
]

export const STATUS_COLORS: Record<string, string> = {
  open: '#3b82f6',
  closed: '#10a37f',
  pending: '#f59e0b',
  overdue: '#ef4444',
  draft: '#6b7280',
  approved: '#10a37f',
  rejected: '#ef4444',
  'in progress': '#3b82f6',
  complete: '#10a37f',
}

// ============== Metric Card ==============
interface MetricCardProps {
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  icon?: ReactNode
  accent?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export const MetricCard = memo(({ 
  label, 
  value, 
  trend, 
  trendValue, 
  icon, 
  accent,
  size = 'md' 
}: MetricCardProps) => {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendColor = trend === 'up' ? '#10a37f' : trend === 'down' ? '#ef4444' : '#6b7280'
  
  const sizes = {
    sm: { value: '24px', label: '11px', padding: '12px' },
    md: { value: '32px', label: '12px', padding: '16px' },
    lg: { value: '42px', label: '14px', padding: '20px' },
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={accent ? 'metric-card accent' : 'metric-card'}
      style={{ padding: sizes[size].padding }}
    >
      {icon && <div style={{ marginBottom: 8, color: 'var(--accent)' }}>{icon}</div>}
      <div style={{ 
        fontSize: sizes[size].value, 
        fontWeight: 700, 
        fontVariantNumeric: 'tabular-nums',
        color: accent ? 'var(--accent)' : 'var(--text-primary)'
      }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div style={{ 
        fontSize: sizes[size].label, 
        color: 'var(--text-muted)', 
        marginTop: 4,
        textTransform: 'uppercase',
        letterSpacing: '0.05em'
      }}>
        {label}
      </div>
      {trend && trendValue && (
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 4, 
          marginTop: 8,
          fontSize: 12,
          color: trendColor
        }}>
          <TrendIcon size={14} />
          <span>{trendValue}</span>
        </div>
      )}
    </motion.div>
  )
})

// ============== Metrics Grid ==============
interface MetricsGridProps {
  children: ReactNode
  columns?: number
}

export const MetricsGrid = ({ children, columns = 4 }: MetricsGridProps) => (
  <div style={{
    display: 'grid',
    gridTemplateColumns: `repeat(auto-fit, minmax(${100 / columns}%, 1fr))`,
    gap: 12,
    margin: '16px 0'
  }}>
    {children}
  </div>
)

// ============== Inline Charts ==============
interface ChartData {
  name: string
  value: number
  [key: string]: any
}

interface InlineChartProps {
  type: 'pie' | 'bar' | 'horizontal_bar' | 'line'
  data: ChartData[]
  title?: string
  height?: number
  showLegend?: boolean
  valueFormatter?: (value: number) => string
}

export const InlineChart = memo(({ 
  type, 
  data, 
  title, 
  height = 250,
  showLegend = true,
  valueFormatter = (v) => v.toLocaleString()
}: InlineChartProps) => {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null
    return (
      <div style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: 8,
        padding: '10px 14px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
      }}>
        <p style={{ fontWeight: 600, marginBottom: 4 }}>{label || payload[0].name}</p>
        <p style={{ color: 'var(--accent)', fontSize: 14 }}>
          {valueFormatter(payload[0].value)}
        </p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: 12,
        padding: 20,
        margin: '16px 0'
      }}
    >
      {title && (
        <h4 style={{ 
          fontSize: 14, 
          fontWeight: 600, 
          marginBottom: 16,
          color: 'var(--text-primary)'
        }}>
          {title}
        </h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        {type === 'pie' ? (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
              animationDuration={500}
            >
              {data.map((_, idx) => (
                <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
          </PieChart>
        ) : type === 'bar' || type === 'horizontal_bar' ? (
          <BarChart 
            data={data} 
            layout={type === 'horizontal_bar' ? 'vertical' : 'horizontal'}
            margin={{ left: type === 'horizontal_bar' ? 80 : 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            {type === 'horizontal_bar' ? (
              <>
                <XAxis type="number" stroke="var(--text-muted)" fontSize={12} />
                <YAxis type="category" dataKey="name" stroke="var(--text-muted)" fontSize={12} width={75} />
              </>
            ) : (
              <>
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
                <YAxis stroke="var(--text-muted)" fontSize={12} />
              </>
            )}
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} animationDuration={500} />
          </BarChart>
        ) : (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
            <YAxis stroke="var(--text-muted)" fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke={CHART_COLORS[0]} 
              strokeWidth={2}
              dot={{ fill: CHART_COLORS[0], r: 4 }}
              animationDuration={500}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </motion.div>
  )
})

// ============== Status Badge ==============
interface StatusBadgeProps {
  status: string
  size?: 'sm' | 'md'
}

export const StatusBadge = memo(({ status, size = 'md' }: StatusBadgeProps) => {
  const normalized = status.toLowerCase()
  const color = STATUS_COLORS[normalized] || '#6b7280'
  
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: size === 'sm' ? '2px 8px' : '4px 12px',
      borderRadius: 20,
      fontSize: size === 'sm' ? 11 : 12,
      fontWeight: 500,
      background: `${color}20`,
      color: color
    }}>
      <span style={{
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: color
      }} />
      {status}
    </span>
  )
})

// ============== Progress Bar ==============
interface ProgressBarProps {
  value: number
  max?: number
  label?: string
  showPercentage?: boolean
  color?: string
  size?: 'sm' | 'md' | 'lg'
}

export const ProgressBar = memo(({ 
  value, 
  max = 100, 
  label, 
  showPercentage = true,
  color = 'var(--accent)',
  size = 'md'
}: ProgressBarProps) => {
  const percentage = Math.min((value / max) * 100, 100)
  const heights = { sm: 6, md: 10, lg: 14 }
  
  return (
    <div style={{ margin: '8px 0' }}>
      {(label || showPercentage) && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: 6,
          fontSize: 13
        }}>
          {label && <span style={{ color: 'var(--text-secondary)' }}>{label}</span>}
          {showPercentage && <span style={{ color: 'var(--text-muted)' }}>{percentage.toFixed(0)}%</span>}
        </div>
      )}
      <div style={{
        width: '100%',
        height: heights[size],
        background: 'var(--bg-tertiary)',
        borderRadius: heights[size] / 2,
        overflow: 'hidden'
      }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          style={{
            height: '100%',
            background: color,
            borderRadius: heights[size] / 2
          }}
        />
      </div>
    </div>
  )
})

// ============== Insight Callout ==============
interface InsightCalloutProps {
  type: 'success' | 'warning' | 'danger' | 'info'
  title: string
  children: ReactNode
}

export const InsightCallout = memo(({ type, title, children }: InsightCalloutProps) => {
  const configs = {
    success: { icon: CheckCircle2, color: '#10a37f', bg: 'rgba(16, 163, 127, 0.08)' },
    warning: { icon: AlertTriangle, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.08)' },
    danger: { icon: AlertTriangle, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.08)' },
    info: { icon: Sparkles, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.08)' }
  }
  
  const config = configs[type]
  const Icon = config.icon
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      style={{
        display: 'flex',
        gap: 14,
        padding: 16,
        background: config.bg,
        border: `1px solid ${config.color}30`,
        borderRadius: 10,
        margin: '16px 0'
      }}
    >
      <Icon size={20} style={{ color: config.color, flexShrink: 0, marginTop: 2 }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          {children}
        </div>
      </div>
    </motion.div>
  )
})

// ============== Entity Card ==============
interface EntityCardProps {
  type: 'rfi' | 'contract' | 'punch' | 'submittal' | 'project'
  title: string
  subtitle?: string
  status?: string
  metadata?: { label: string; value: string }[]
  actions?: { label: string; onClick: () => void; primary?: boolean }[]
}

const ENTITY_ICONS: Record<string, { emoji: string; color: string }> = {
  rfi: { emoji: '📋', color: 'rgba(59, 130, 246, 0.15)' },
  contract: { emoji: '💰', color: 'rgba(16, 163, 127, 0.15)' },
  punch: { emoji: '✅', color: 'rgba(239, 68, 68, 0.15)' },
  submittal: { emoji: '📁', color: 'rgba(168, 85, 247, 0.15)' },
  project: { emoji: '🏗️', color: 'rgba(245, 158, 11, 0.15)' },
}

export const EntityCard = memo(({ type, title, subtitle, status, metadata, actions }: EntityCardProps) => {
  const icon = ENTITY_ICONS[type] || ENTITY_ICONS.project
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: 12,
        padding: 16,
        margin: '12px 0'
      }}
    >
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
        <div style={{
          width: 44,
          height: 44,
          borderRadius: 10,
          background: icon.color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 20,
          flexShrink: 0
        }}>
          {icon.emoji}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <h4 style={{ 
              fontSize: 15, 
              fontWeight: 600, 
              margin: 0,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}>
              {title}
            </h4>
            {status && <StatusBadge status={status} size="sm" />}
          </div>
          {subtitle && (
            <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>{subtitle}</p>
          )}
          {metadata && metadata.length > 0 && (
            <div style={{ 
              display: 'flex', 
              gap: 16, 
              marginTop: 10,
              flexWrap: 'wrap'
            }}>
              {metadata.map((m, i) => (
                <div key={i} style={{ fontSize: 12 }}>
                  <span style={{ color: 'var(--text-muted)' }}>{m.label}: </span>
                  <span style={{ color: 'var(--text-secondary)' }}>{m.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      {actions && actions.length > 0 && (
        <div style={{ display: 'flex', gap: 8, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-color)' }}>
          {actions.map((action, i) => (
            <button
              key={i}
              onClick={action.onClick}
              style={{
                padding: '6px 14px',
                borderRadius: 6,
                border: action.primary ? 'none' : '1px solid var(--border-color)',
                background: action.primary ? 'var(--accent)' : 'transparent',
                color: action.primary ? 'white' : 'var(--text-secondary)',
                fontSize: 13,
                cursor: 'pointer'
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </motion.div>
  )
})

// ============== Collapsible Section ==============
interface CollapsibleProps {
  title: string
  defaultOpen?: boolean
  children: ReactNode
  badge?: string | number
}

export const Collapsible = memo(({ title, defaultOpen = false, children, badge }: CollapsibleProps) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  
  return (
    <div style={{ margin: '12px 0' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '12px 16px',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: isOpen ? '10px 10px 0 0' : 10,
          color: 'var(--text-primary)',
          fontSize: 14,
          fontWeight: 600,
          cursor: 'pointer',
          textAlign: 'left'
        }}
      >
        {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        <span style={{ flex: 1 }}>{title}</span>
        {badge !== undefined && (
          <span style={{
            padding: '2px 10px',
            background: 'var(--bg-tertiary)',
            borderRadius: 12,
            fontSize: 12,
            color: 'var(--text-muted)'
          }}>
            {badge}
          </span>
        )}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{
              overflow: 'hidden',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderTop: 'none',
              borderRadius: '0 0 10px 10px'
            }}
          >
            <div style={{ padding: 16 }}>
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
})

// ============== Data Table ==============
interface DataTableProps {
  columns: { key: string; label: string; width?: string; align?: 'left' | 'center' | 'right' }[]
  data: Record<string, any>[]
  maxRows?: number
  onRowClick?: (row: Record<string, any>) => void
}

export const DataTable = memo(({ columns, data, maxRows = 10, onRowClick }: DataTableProps) => {
  const displayData = data.slice(0, maxRows)
  const hasMore = data.length > maxRows
  
  return (
    <div style={{ 
      margin: '16px 0',
      borderRadius: 10,
      border: '1px solid var(--border-color)',
      overflow: 'hidden'
    }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--bg-tertiary)' }}>
              {columns.map(col => (
                <th
                  key={col.key}
                  style={{
                    padding: '12px 16px',
                    textAlign: col.align || 'left',
                    fontSize: 12,
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    borderBottom: '1px solid var(--border-color)',
                    width: col.width,
                    whiteSpace: 'nowrap'
                  }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, idx) => (
              <motion.tr
                key={idx}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: idx * 0.03 }}
                onClick={() => onRowClick?.(row)}
                style={{ 
                  cursor: onRowClick ? 'pointer' : 'default',
                  background: idx % 2 === 0 ? 'transparent' : 'var(--bg-secondary)'
                }}
              >
                {columns.map(col => {
                  const value = row[col.key]
                  // Auto-detect status columns
                  const isStatus = col.key.toLowerCase().includes('status')
                  
                  return (
                    <td
                      key={col.key}
                      style={{
                        padding: '10px 16px',
                        fontSize: 13,
                        color: 'var(--text-secondary)',
                        borderBottom: '1px solid var(--border-color)',
                        textAlign: col.align || 'left'
                      }}
                    >
                      {isStatus && value ? (
                        <StatusBadge status={String(value)} size="sm" />
                      ) : (
                        String(value ?? '')
                      )}
                    </td>
                  )
                })}
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasMore && (
        <div style={{
          padding: '10px 16px',
          background: 'var(--bg-tertiary)',
          fontSize: 12,
          color: 'var(--text-muted)',
          textAlign: 'center'
        }}>
          Showing {maxRows} of {data.length} rows
        </div>
      )}
    </div>
  )
})

// ============== Report Download Button ==============
interface ReportDownloadProps {
  url: string
  filename: string
  title?: string
}

export const ReportDownload = memo(({ url, filename, title }: ReportDownloadProps) => (
  <motion.a
    href={url}
    target="_blank"
    rel="noopener noreferrer"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 12,
      padding: '16px 24px',
      background: 'linear-gradient(135deg, var(--accent) 0%, #0e8a6c 100%)',
      color: 'white',
      borderRadius: 12,
      textDecoration: 'none',
      fontWeight: 600,
      fontSize: 15,
      margin: '16px 0',
      boxShadow: '0 4px 16px rgba(16, 163, 127, 0.3)'
    }}
  >
    <FileText size={20} />
    <span>{title || filename}</span>
    <Download size={18} style={{ marginLeft: 'auto' }} />
  </motion.a>
))

// ============== Tool Activity Indicator ==============
interface ToolActivityProps {
  toolName: string
  status: 'running' | 'complete' | 'error'
  duration?: number
}

export const ToolActivity = memo(({ toolName, status, duration }: ToolActivityProps) => {
  const toolLabels: Record<string, { label: string; icon: ReactNode }> = {
    find_project: { label: 'Finding project', icon: <SearchIcon size={14} /> },
    discover_environment: { label: 'Discovering data', icon: <Database size={14} /> },
    query_entities: { label: 'Querying records', icon: <Filter size={14} /> },
    generate_report: { label: 'Generating report', icon: <FileText size={14} /> },
    list_report_templates: { label: 'Loading templates', icon: <FileText size={14} /> },
    generate_report_from_template: { label: 'Building report', icon: <FileText size={14} /> },
  }
  
  const tool = toolLabels[toolName] || { label: toolName, icon: <Zap size={14} /> }
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 10 }}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 12px',
        background: 'var(--bg-tertiary)',
        border: '1px solid var(--border-color)',
        borderRadius: 20,
        fontSize: 12,
        color: 'var(--text-secondary)'
      }}
    >
      {status === 'running' ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          {tool.icon}
        </motion.div>
      ) : (
        tool.icon
      )}
      <span>{tool.label}</span>
      {status === 'complete' && duration && (
        <span style={{ color: 'var(--text-muted)' }}>
          {(duration / 1000).toFixed(1)}s
        </span>
      )}
      {status === 'complete' && (
        <CheckCircle2 size={14} style={{ color: 'var(--accent)' }} />
      )}
    </motion.div>
  )
})

// ============== Typing Indicator ==============
export const TypingIndicator = memo(() => (
  <div style={{ display: 'flex', gap: 4, padding: '8px 0' }}>
    {[0, 1, 2].map(i => (
      <motion.div
        key={i}
        animate={{ 
          y: [0, -6, 0],
          opacity: [0.4, 1, 0.4]
        }}
        transition={{
          duration: 0.6,
          repeat: Infinity,
          delay: i * 0.15
        }}
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: 'var(--accent)'
        }}
      />
    ))}
  </div>
))

// ============== Keyboard Shortcut Hint ==============
interface ShortcutHintProps {
  keys: string[]
  label: string
}

export const ShortcutHint = memo(({ keys, label }: ShortcutHintProps) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
    <div style={{ display: 'flex', gap: 4 }}>
      {keys.map((key, i) => (
        <React.Fragment key={i}>
          <kbd style={{
            padding: '2px 6px',
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-color)',
            borderRadius: 4,
            fontSize: 11,
            fontFamily: 'inherit'
          }}>
            {key}
          </kbd>
          {i < keys.length - 1 && <span style={{ color: 'var(--text-muted)' }}>+</span>}
        </React.Fragment>
      ))}
    </div>
    <span style={{ color: 'var(--text-muted)' }}>{label}</span>
  </div>
))
