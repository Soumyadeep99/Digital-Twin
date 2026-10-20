from datetime import datetime
from pydantic import BaseModel,ConfigDict,Field
class PatientCreate(BaseModel):
 id:int|None=Field(default=None,ge=1)
 name:str=Field(min_length=1,max_length=120)
 sex:str=Field(min_length=1,max_length=20)
 age:int=Field(ge=0,le=120)
 diabetes_type:str=Field(pattern="^(type_1|type_2|gestational|other)$")
 hba1c:float|None=Field(default=None,ge=2,le=20)
 bmi:float|None=Field(default=None,ge=5,le=100)
 medications:str=Field(default="",max_length=500)
class PatientOut(PatientCreate):
 model_config=ConfigDict(from_attributes=True)
 id:int
 sex:str|None=None
class ReadingCreate(BaseModel):
 timestamp:datetime
 glucose:float=Field(ge=20,le=600)
 heart_rate:float|None=Field(default=None,ge=20,le=250)
 activity:float|None=Field(default=None,ge=0)
 mets:float|None=Field(default=None,ge=0,le=100)
class ReadingOut(ReadingCreate):
 model_config=ConfigDict(from_attributes=True)
 id:int
 patient_id:int
class PredictionRequest(BaseModel):
 patient_id:int
 readings:list[ReadingCreate]=Field(min_length=180,max_length=180)
class PredictionPoint(BaseModel):
 timestamp:datetime
 glucose:float
class PredictionResponse(BaseModel):
 predictions:list[PredictionPoint]
 max_predicted_rise:float
 spike_flag:bool
 label:str="Research estimate only; not a medical diagnosis."
 model:str
class SimulationRequest(BaseModel):
 patient_id:int
 subject_id:int=Field(default=1,ge=1,le=999)
 limit:int=Field(default=24,ge=1,le=500)
 start_at:datetime|None=None
