import os, zipfile
from pathlib import Path
import pandas as pd
from ..schemas import ReadingCreate

class SimulationError(RuntimeError): pass

def sample_readings(subject_id: int, limit: int, start_at=None):
    configured=os.getenv('CGMACROS_ZIP',str(Path(__file__).resolve().parents[2]/'CGMacros_dateshifted365 (1).zip'))
    path=Path(configured)
    if not path.exists(): raise SimulationError(f'CGMacros ZIP not found: {path}')
    internal=f'CGMacros/CGMacros-{subject_id:03d}/CGMacros-{subject_id:03d}.csv'
    try:
        with zipfile.ZipFile(path) as z:
            with z.open(internal) as f: frame=pd.read_csv(f)
    except KeyError as e: raise SimulationError(f'Subject {subject_id} is not in the CGMacros archive') from e
    frame['Timestamp']=pd.to_datetime(frame['Timestamp'],errors='coerce')
    frame=frame.dropna(subset=['Timestamp']).sort_values('Timestamp')
    # CGMacros is minute-level; retain the five-minute samples used by the trained sequence split.
    frame=frame[frame.Timestamp.dt.minute % 5 == 0].copy()
    glucose=frame['Libre GL'].combine_first(frame['Dexcom GL'])
    frame=frame[glucose.notna()].copy(); frame['glucose']=glucose[glucose.notna()]
    frame=frame.tail(limit)
    if len(frame)==0: raise SimulationError('No glucose observations found for this subject')
    if start_at is not None:
        start=start_at.replace(tzinfo=None)
        frame=frame.reset_index(drop=True)
        frame['Timestamp']=[start+pd.Timedelta(minutes=5*i) for i in range(len(frame))]
    def num(row,col):
        v=row.get(col)
        return None if pd.isna(v) else float(v)
    return [ReadingCreate(timestamp=r.Timestamp.to_pydatetime(),glucose=float(r.glucose),heart_rate=num(r,'HR'),activity=num(r,'Calories (Activity)'),mets=num(r,'METs')) for _,r in frame.iterrows()]
