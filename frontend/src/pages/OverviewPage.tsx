import { Activity, ArrowRight, Droplets, Heart, Radio, ShieldAlert, Users } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, EmptyState, ErrorState, Loading, PageHeading } from '../components/UI'
import { GlucoseChart, MetricCard, PatientAvatar, StatusPill } from '../components/DataViz'
import { apiService, errorMessage } from '../services/api'
import type { ModelStatus, Patient, Reading } from '../types/api'

interface Row { patient: Patient; readings: Reading[] }
export function OverviewPage() {
  const [rows, setRows] = useState<Row[]>([])
  const [model, setModel] = useState<ModelStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<number | null>(null)
  const load = async () => {
    setLoading(true); setError('')
    try {
      const patients = await apiService.patients()
      const data = await Promise.all(patients.map(async patient => ({ patient, readings: await apiService.readings(patient.id, 36) })))
      setRows(data); setSelected(current => data.some(x => x.patient.id === current) ? current : data[0]?.patient.id ?? null)
      setModel(await apiService.modelStatus())
    } catch (e) { setError(errorMessage(e)) } finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [])
  const all = useMemo(() => rows.flatMap(r => r.readings).sort((a,b) => new Date(b.timestamp).getTime()-new Date(a.timestamp).getTime()), [rows])
  const latest = all[0]
  const activeRow = rows.find(r => r.patient.id === selected)
  const recent = all.slice(0,5).map(r => ({ reading: r, patient: rows.find(x => x.patient.id === r.patient_id)?.patient }))
  return <>
    <PageHeading eyebrow={new Intl.DateTimeFormat(undefined,{weekday:"long",day:"2-digit",month:"long",year:"numeric"}).format(new Date()).toUpperCase()} title="Overview" description="A clear view of patient readings and monitoring activity." action={<Link className="button button-primary" to="/patients"><Users size={16}/> View patients</Link>}/>
    {error && <ErrorState message={error} onRetry={() => void load()}/>}
    {loading ? <Loading label="Loading patient data…"/> : <>
      <div className="metric-grid">
        <MetricCard label="Total patients" value={rows.length} note="Patient records in workspace" icon={<Users size={18}/>} tone="blue"/>
        <MetricCard label="Latest glucose" value={latest ? latest.glucose.toFixed(0) : '—'} unit={latest ? 'mg/dL' : ''} note={latest ? `Recorded ${new Date(latest.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}` : 'No readings recorded'} icon={<Droplets size={18}/>} tone="teal"/>
        <MetricCard label="Latest heart rate" value={latest?.heart_rate?.toFixed(0) ?? '—'} unit={latest?.heart_rate != null ? 'bpm' : ''} note="Most recent recorded reading" icon={<Heart size={18}/>} tone="blue"/>
        <MetricCard label="Patients at risk" value="Unavailable" note="Verified forecasting is not enabled" icon={<ShieldAlert size={18}/>} tone="amber"/>
      </div>
      {!model?.inference_ready && <div className="inline-callout"><ShieldAlert size={18}/><div><strong>Glucose risk estimates are unavailable</strong><span>The original model and preprocessing files are missing. The app will not display unverified forecasts or risk flags.</span></div><Link to={rows[0] ? `/predictions/${rows[0].patient.id}` : '/patients'}>View details <ArrowRight size={14}/></Link></div>}
      <div className="overview-grid">
        <Card title="Glucose trends" subtitle="Recent readings from a selected patient" action={activeRow && <Link className="text-link" to={`/patients/${activeRow.patient.id}`}>View profile <ArrowRight size={14}/></Link>}>
          {rows.length > 0 && <div className="select-row"><label htmlFor="overview-patient">Patient</label><select id="overview-patient" value={selected ?? ''} onChange={e => setSelected(Number(e.target.value))}>{rows.map(r => <option key={r.patient.id} value={r.patient.id}>{r.patient.name}</option>)}</select></div>}
          {activeRow?.readings.length ? <GlucoseChart readings={activeRow.readings}/> : <EmptyState title="No trend data" message="Add readings or replay a CGMacros sample to see a glucose trend."/>}
        </Card>
        <Card title="Patient risk overview" subtitle="Risk labels require a verified forecast">
          {rows.length === 0 ? <EmptyState title="No patient records" message="Patient records will appear here when available."/> : <div className="risk-list">{rows.slice(0,5).map(({patient,readings}) => <div className="risk-row" key={patient.id}><PatientAvatar name={patient.name}/><div className="risk-person"><Link to={`/patients/${patient.id}`}>{patient.name}</Link><span>{readings[readings.length-1] ? `${readings[readings.length-1]?.glucose.toFixed(0)} mg/dL · latest reading` : 'No readings yet'}</span></div><StatusPill>Not assessed</StatusPill></div>)}</div>}
          <div className="risk-footnote"><ShieldAlert size={14}/> No clinical risk classification is available.</div>
        </Card>
      </div>
      <div className="overview-grid overview-grid-lower">
        <Card title="Recent monitoring activity" subtitle="Most recent recorded patient readings" action={<Link to="/live" className="text-link"><Radio size={15}/> Live monitoring</Link>}>
          {recent.length === 0 ? <EmptyState title="No recent activity" message="New readings will appear here after recording or sample replay."/> : <div className="activity-list">{recent.map(({reading,patient},i) => <div className="activity-row" key={`${reading.id ?? reading.timestamp}-${i}`}><span className="activity-indicator"><Activity size={15}/></span><p><strong>{patient?.name ?? `Patient ${reading.patient_id ?? ''}`}</strong><span>Glucose reading · {reading.glucose.toFixed(0)} mg/dL</span></p><time>{new Date(reading.timestamp).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}</time></div>)}</div>}
        </Card>
        <Card title="Model availability" subtitle="Checkpoint readiness for glucose forecasting">
          <div className="model-status-row"><span className={`model-status-icon ${model?.inference_ready ? 'model-ready' : ''}`}><Radio size={18}/></span><div><strong>{model?.inference_ready ? 'Forecasting ready' : 'Forecasting unavailable'}</strong><span>{model?.checkpoint ?? 'Checking model…'} {model?.checkpoint_loaded ? 'loaded' : 'not loaded'}</span></div><StatusPill tone={model?.inference_ready ? 'good' : 'warning'}>{model?.inference_ready ? 'Ready' : 'Needs model files'}</StatusPill></div>
          <p className="subtle-copy">Predictions are shown only when the original model implementation and input preparation can be verified.</p>
          <Link className="button button-secondary button-full" to={rows[0] ? `/predictions/${rows[0].patient.id}` : '/patients'}>Open predictions <ArrowRight size={16}/></Link>
        </Card>
      </div>
    </>}
  </>
}
