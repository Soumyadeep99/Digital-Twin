import { AlertCircle, CheckCircle2, Info } from 'lucide-react'
import type { ReactNode } from 'react'

export function PageHeading({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="page-heading"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <div className="heading-action">{action}</div>}</div>
}
export function Card({ title, subtitle, action, children, className = '' }: { title?: string; subtitle?: string; action?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={`card ${className}`}>{(title || subtitle || action) && <div className="card-heading"><div>{title && <h2>{title}</h2>}{subtitle && <p>{subtitle}</p>}</div>{action}</div>}{children}</section>
}
export function Loading({ label = 'Loading data…' }: { label?: string }) { return <div className="loading-state"><span className="spinner" aria-hidden="true"/><span>{label}</span></div> }
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) { return <div className="notice notice-error" role="alert"><AlertCircle size={18}/><div><strong>Unable to load data</strong><p>{message}</p>{onRetry && <button className="text-button" onClick={onRetry}>Try again</button>}</div></div> }
export function InfoNotice({ children }: { children: ReactNode }) { return <div className="notice notice-info"><Info size={18}/><div>{children}</div></div> }
export function SuccessNotice({ children }: { children: ReactNode }) { return <div className="notice notice-success"><CheckCircle2 size={18}/><div>{children}</div></div> }
export function EmptyState({ title, message }: { title: string; message: string }) { return <div className="empty-state"><div className="empty-icon"><Info size={20}/></div><strong>{title}</strong><p>{message}</p></div> }
