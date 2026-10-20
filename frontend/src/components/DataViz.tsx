import { lazy, Suspense } from 'react'
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import type { ReactNode } from 'react'
import type { Reading, PredictionPoint } from '../types/api'

const GlucoseChartModule = lazy(() => import('./GlucoseChartModule'))

export function MetricCard({ label, value, unit, note, icon, tone = 'teal' }: { label: string; value: string | number; unit?: string; note?: string; icon: ReactNode; tone?: 'teal' | 'blue' | 'amber' | 'slate' }) {
  return <div className="metric-card"><div className="metric-top"><span>{label}</span><span className={`metric-icon metric-${tone}`}>{icon}</span></div><div className="metric-value">{value}<small>{unit}</small></div>{note && <div className="metric-note">{note}</div>}</div>
}

export function GlucoseChart(props: { readings: Reading[]; predictions?: PredictionPoint[]; compact?: boolean }) {
  return <Suspense fallback={<div className="chart-empty">Preparing chart…</div>}><GlucoseChartModule {...props}/></Suspense>
}

export function StatusPill({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'good' | 'warning' | 'neutral' }) { return <span className={`status-pill status-${tone}`}>{children}</span> }
export function TrendIcon({ value }: { value: number }) { return value > 0 ? <ArrowUpRight size={15}/> : value < 0 ? <ArrowDownRight size={15}/> : <Minus size={15}/> }
export function PatientAvatar({ name }: { name: string }) { return <span className="patient-avatar" aria-label={name}>{name.split(/\s+/).map(part => part[0]).join('').slice(0,2).toUpperCase()}</span> }
