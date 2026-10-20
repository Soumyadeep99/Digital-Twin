from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import GlucoseReading, Patient
from ..schemas import SimulationRequest
from ..services.simulation import sample_readings, SimulationError
router=APIRouter(prefix='/simulation',tags=['simulation'])

@router.post('/replay')
def replay(request: SimulationRequest, db: Session=Depends(get_db)):
    if not db.get(Patient,request.patient_id): raise HTTPException(404,'Patient not found')
    try: readings=sample_readings(request.subject_id,request.limit,request.start_at)
    except SimulationError as e: raise HTTPException(422,str(e)) from e
    records=[GlucoseReading(patient_id=request.patient_id,**r.model_dump()) for r in readings]
    db.add_all(records); db.commit()
    return {'inserted':len(records),'subject_id':request.subject_id,'patient_id':request.patient_id,'first_timestamp':records[0].timestamp,'last_timestamp':records[-1].timestamp}
