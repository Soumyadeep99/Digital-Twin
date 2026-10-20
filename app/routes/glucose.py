from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import GlucoseReading,Patient
from ..schemas import ReadingCreate,ReadingOut
router=APIRouter(prefix="/patients/{patient_id}/readings",tags=["glucose"])
@router.post("",response_model=ReadingOut,status_code=201)
def add_reading(patient_id:int,reading:ReadingCreate,db:Session=Depends(get_db)):
 if not db.get(Patient,patient_id): raise HTTPException(404,"Patient not found")
 record=GlucoseReading(patient_id=patient_id,**reading.model_dump()); db.add(record); db.commit(); db.refresh(record); return record
@router.get("",response_model=list[ReadingOut])
def list_readings(patient_id:int,limit:int=Query(180,ge=1,le=5000),db:Session=Depends(get_db)):
 if not db.get(Patient,patient_id): raise HTTPException(404,"Patient not found")
 return db.query(GlucoseReading).filter_by(patient_id=patient_id).order_by(GlucoseReading.timestamp.desc()).limit(limit).all()[::-1]
