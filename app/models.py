from datetime import datetime
from sqlalchemy import DateTime,Float,ForeignKey,Integer,String
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .database import Base
class Patient(Base):
 __tablename__="patients"
 id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
 name:Mapped[str]=mapped_column(String(120),nullable=False)
 sex:Mapped[str|None]=mapped_column(String(20),nullable=True)
 age:Mapped[int]=mapped_column(Integer,nullable=False)
 diabetes_type:Mapped[str]=mapped_column(String(30),nullable=False)
 hba1c:Mapped[float|None]=mapped_column(Float)
 bmi:Mapped[float|None]=mapped_column(Float)
 medications:Mapped[str]=mapped_column(String(500),default="")
 readings:Mapped[list["GlucoseReading"]]=relationship(back_populates="patient",cascade="all, delete-orphan")
class GlucoseReading(Base):
 __tablename__="glucose_readings"
 id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
 patient_id:Mapped[int]=mapped_column(ForeignKey("patients.id"),index=True)
 timestamp:Mapped[datetime]=mapped_column(DateTime,nullable=False,index=True)
 glucose:Mapped[float]=mapped_column(Float,nullable=False)
 heart_rate:Mapped[float|None]=mapped_column(Float)
 activity:Mapped[float|None]=mapped_column(Float)
 mets:Mapped[float|None]=mapped_column(Float)
 patient:Mapped[Patient]=relationship(back_populates="readings")
