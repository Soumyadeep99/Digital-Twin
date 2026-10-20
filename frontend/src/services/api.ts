import type { Patient, PatientCreate, Reading, PredictionResponse, ModelStatus, ReplayResult } from '../types/api'
import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000', timeout: 12000 })

export const apiService = {
  async health() { return (await api.get<{ status: string }>('/health')).data },
  async patients() { return (await api.get<Patient[]>('/patients')).data },
  async createPatient(patient: PatientCreate) { return (await api.post<Patient>('/patients', patient)).data },
  async patient(id: number) { return (await api.get<Patient>(`/patients/${id}`)).data },
  async readings(id: number, limit = 180) { return (await api.get<Reading[]>(`/patients/${id}/readings`, { params: { limit } })).data },
  async createReading(id: number, reading: Omit<Reading, 'id' | 'patient_id'>) { return (await api.post<Reading>(`/patients/${id}/readings`, reading)).data },
  async modelStatus() { return (await api.get<ModelStatus>('/predictions/status')).data },
  async forecast(patientId: number, readings: Reading[]) {
    return (await api.post<PredictionResponse>('/predictions/forecast', { patient_id: patientId, readings })).data
  },
  async replay(patientId: number, subjectId: number, limit: number, startAt: string) {
    return (await api.post<ReplayResult>('/simulation/replay', { patient_id: patientId, subject_id: subjectId, limit, start_at: startAt })).data
  },
}

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return 'Could not reach the API. Check that the FastAPI server is running and VITE_API_BASE_URL is correct.'
    const detail = error.response.data?.detail
    if (typeof detail === 'string') return detail
    if (error.response.status === 503) return 'Forecasting is unavailable until the original GluFormer model and preprocessing are provided.'
    return `Request failed (${error.response.status}). Please try again.`
  }
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}
