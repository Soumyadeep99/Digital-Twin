import { useEffect, useState } from 'react'
import { Activity, HeartPulse, LayoutDashboard, Menu, PanelLeftClose, PanelLeftOpen, Radio, Users, X } from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { apiService } from '../services/api'

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/patients', label: 'Patients', icon: Users },
  { to: '/live', label: 'Live monitoring', icon: Radio },
]

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [connected, setConnected] = useState<boolean | null>(null)
  const location = useLocation()
  useEffect(() => { setMobileOpen(false) }, [location.pathname])
  useEffect(() => {
    let active = true
    const check = () => apiService.health().then(() => active && setConnected(true)).catch(() => active && setConnected(false))
    void check()
    const timer = window.setInterval(check, 30000)
    return () => { active = false; window.clearInterval(timer) }
  }, [])
  const title = location.pathname.startsWith('/patients/') ? 'Patient profile' : location.pathname.startsWith('/predictions') ? 'Glucose predictions' : location.pathname === '/patients' ? 'Patients' : location.pathname === '/live' ? 'Live monitoring' : 'Overview'
  return <div className="app-shell">
    {mobileOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''} ${mobileOpen ? 'sidebar-mobile-open' : ''}`}>
      <div className="brand-row"><span className="brand-mark"><Activity size={19}/></span>{!collapsed && <div className="brand-copy"><strong>Carewell</strong><span>Digital Twin</span></div>}<button className="icon-button collapse-toggle" onClick={() => setCollapsed(v => !v)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>{collapsed ? <PanelLeftOpen size={17}/> : <PanelLeftClose size={17}/>}</button><button className="icon-button mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={19}/></button></div>
      {!collapsed && <div className="workspace-label">CLINICAL WORKSPACE</div>}
      <nav className="side-nav" aria-label="Main navigation">
        {navItems.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} title={collapsed ? label : undefined} className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}><Icon size={18}/>{!collapsed && <span>{label}</span>}</NavLink>)}
      </nav>
      {!collapsed && <div className="sidebar-bottom"><div className="sidebar-note-icon"><HeartPulse size={16}/></div><p>Research prototype</p><span>For clinical research use only</span></div>}
    </aside>
    <div className="main-frame">
      <header className="topbar"><button className="icon-button mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div className="breadcrumbs"><span>Workspace</span><span className="crumb-separator">/</span><strong>{title}</strong></div><div className={`connection-pill ${connected === true ? 'connection-ok' : connected === false ? 'connection-down' : ''}`}><span className="connection-dot"/>{connected === null ? 'Checking API' : connected ? 'API connected' : 'API unavailable'}</div><div className="top-avatar" aria-label="Care team">CT</div></header>
      <main className="page-content"><Outlet/></main>
      <footer className="app-footer"><span>Carewell Digital Twin</span><span>Research estimates are not medical diagnoses.</span></footer>
    </div>
  </div>
}
