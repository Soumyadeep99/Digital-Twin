from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Patient
from ..schemas import PatientCreate,PatientOut
router=APIRouter(prefix="/patients",tags=["patients"])
@router.get("",response_model=list[PatientOut])
def list_patients(db:Session=Depends(get_db)): return db.query(Patient).order_by(Patient.id).all()
@router.post("",response_model=PatientOut,status_code=201)
def create_patient(patient:PatientCreate,db:Session=Depends(get_db)):
 values=patient.model_dump(); patient_id=values.pop('id')
 record=Patient(**values)
 if patient_id is not None:
  if db.get(Patient,patient_id): raise HTTPException(409,'Patient ID already exists')
  record.id=patient_id
 db.add(record); db.commit(); db.refresh(record); return record
@router.get("/{patient_id}",response_model=PatientOut)
def get_patient(patient_id:int,db:Session=Depends(get_db)):
 record=db.get(Patient,patient_id)
 if record is None: raise HTTPException(404,"Patient not found")
 return record
