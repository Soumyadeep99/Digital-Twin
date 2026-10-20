from datetime import datetime, timedelta
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Patient
from ..schemas import PredictionRequest, PredictionResponse, PredictionPoint
from ..services.gluformer import service
router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.post("/forecast", response_model=PredictionResponse)
def forecast(payload: PredictionRequest, db: Session = Depends(get_db)):
    if not db.get(Patient, payload.patient_id): raise HTTPException(404, "Patient not found")
    try:
        values=service.predict(payload.readings, subject_id=payload.patient_id)
    except ValueError as e: raise HTTPException(422, str(e)) from e
    except RuntimeError as e: raise HTTPException(503, str(e)) from e
    current=max(payload.readings,key=lambda reading: reading.timestamp).glucose
    rise=max([g-current for _,g in values],default=0)
    return PredictionResponse(predictions=[PredictionPoint(timestamp=t,glucose=g) for t,g in values],max_predicted_rise=round(rise,2),spike_flag=rise>=30,model=service.path.name)

@router.get("/status")
def model_status():
    return {"checkpoint_loaded":service.model is not None,"inference_ready":service.compatibility_confirmed,"checkpoint":service.path.name,"device":str(service.device),"error":service.error}
