from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import JSONResponse
from .database import Base, SessionLocal, engine
from .models import Patient
from sqlalchemy import inspect, text
from .routes import patients_router, glucose_router, predictions_router, simulation_router

app=FastAPI(title='Diabetes Digital Twin API',version='0.1.0',description='Research prototype; glucose spike risk is not a medical diagnosis.')
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in os.getenv('FRONTEND_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(',')], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)
    if 'sex' not in {column['name'] for column in inspect(engine).get_columns('patients')}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE patients ADD COLUMN sex VARCHAR(20)"))
    db=SessionLocal()
    try:
        if db.query(Patient).count()==0:
            db.add_all([
                Patient(name='Synthetic Patient 1',age=45,diabetes_type='type_2',hba1c=7.2,bmi=28.4,medications='metformin'),
                Patient(name='Synthetic Patient 2',age=31,diabetes_type='type_1',hba1c=6.8,bmi=24.1,medications='insulin'),
                Patient(name='Synthetic Patient 3',age=57,diabetes_type='type_2',hba1c=8.1,bmi=31.2,medications='metformin; GLP-1 receptor agonist'),
            ]); db.commit()
    finally: db.close()

@app.get('/health',tags=['health'])
def health(): return {'status':'ok'}

app.include_router(patients_router); app.include_router(glucose_router); app.include_router(predictions_router); app.include_router(simulation_router)
