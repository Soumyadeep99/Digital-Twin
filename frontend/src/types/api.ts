export interface Patient {
  id: number
  name: string
  sex: string | null
  age: number
  diabetes_type: 'type_1' | 'type_2' | 'gestational' | 'other'
  hba1c: number | null
  bmi: number | null
  medications: string
}
export type PatientCreate = Omit<Patient, 'sex' | 'id'> & { id?: number; sex: string }
export interface Reading {
  id?: number
  patient_id?: number
  timestamp: string
  glucose: number
  heart_rate: number | null
  activity: number | null
  mets: number | null
}
export interface PredictionPoint { timestamp: string; glucose: number }
export interface PredictionResponse {
  predictions: PredictionPoint[]
  max_predicted_rise: number
  spike_flag: boolean
  label: string
  model: string
}
export interface ModelStatus {
  checkpoint_loaded: boolean
  inference_ready: boolean
  checkpoint: string
  device: string
  error: string | null
}
export interface ReplayResult {
  inserted: number
  subject_id: number
  patient_id: number
  first_timestamp: string
  last_timestamp: string
}
export interface PatientData { patient: Patient; readings: Reading[] }
