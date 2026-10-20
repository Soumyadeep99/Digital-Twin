import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { OverviewPage } from './pages/OverviewPage'
import { PatientsPage } from './pages/PatientsPage'
import { PatientDetailPage } from './pages/PatientDetailPage'
import { PredictionsPage } from './pages/PredictionsPage'
import { LiveMonitoringPage } from './pages/LiveMonitoringPage'
import './index.css'

export default function App(){return <BrowserRouter><Routes><Route element={<AppLayout/>}><Route index element={<OverviewPage/>}/><Route path="patients" element={<PatientsPage/>}/><Route path="patients/:id" element={<PatientDetailPage/>}/><Route path="predictions/:patientId" element={<PredictionsPage/>}/><Route path="live" element={<LiveMonitoringPage/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Route></Routes></BrowserRouter>}
