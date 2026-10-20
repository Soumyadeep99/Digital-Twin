import { Line, LineChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from 'recharts'
import type { Reading, PredictionPoint } from '../types/api'

export default function GlucoseChartModule({ readings, predictions = [], compact = false }: { readings: Reading[]; predictions?: PredictionPoint[]; compact?: boolean }) {
  const data = [
    ...readings.map((r, i) => ({ time: new Date(r.timestamp).getTime(), actual: r.glucose, predicted: predictions.length > 0 && i === readings.length - 1 ? r.glucose : undefined as number | undefined })),
    ...predictions.map(p => ({ time: new Date(p.timestamp).getTime(), actual: undefined as number | undefined, predicted: p.glucose })),
  ].sort((a,b) => a.time-b.time).map(p => ({ ...p, label: new Date(p.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }))
  if (!data.length) return <div className="chart-empty">No glucose readings have been recorded yet.</div>
  return <div className={`chart-wrap ${compact ? 'chart-compact' : ''}`}><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ top: 12, right: 12, bottom: 0, left: -15 }}>
    <CartesianGrid stroke="#e8eef1" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="label" tick={{ fontSize: 11, fill: '#8091a0' }} tickLine={false} axisLine={false} minTickGap={28}/><YAxis tick={{ fontSize: 11, fill: '#8091a0' }} tickLine={false} axisLine={false} domain={['auto','auto']} width={48} label={compact ? undefined : { value: 'mg/dL', angle: -90, position: 'insideLeft', fill: '#8495a2', fontSize: 11 }}/><Tooltip labelFormatter={(label, payload) => { const time = payload[0]?.payload?.time as number | undefined; return time ? new Date(time).toLocaleString() : String(label) }} formatter={(value, name) => [`${Number(value).toFixed(1)} mg/dL`, name === 'actual' ? 'Observed' : 'Forecast']}/>
    <ReferenceLine y={180} stroke="#d6a759" strokeDasharray="4 4" ifOverflow="extendDomain"/><Line type="monotone" dataKey="actual" name="Observed" stroke="#267d8a" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} connectNulls={false}/><Line type="monotone" dataKey="predicted" name="Forecast" stroke="#5679a7" strokeWidth={2.5} strokeDasharray="6 5" dot={{ r: 3, fill: '#5679a7' }} connectNulls={false}/>
  </LineChart></ResponsiveContainer>{predictions.length > 0 && <div className="chart-legend"><span><i className="legend-observed"/> Observed</span><span><i className="legend-forecast"/> Forecast</span></div>}</div>
}
