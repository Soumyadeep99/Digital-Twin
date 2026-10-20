from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app

def test_health_and_patient_routes():
    with TestClient(app) as client:
        assert client.get("/health").json()=={"status":"ok"}
        patients=client.get("/patients").json()
        assert len(patients)>=3
        assert patients[0]["name"].startswith("Synthetic Patient")
        detail=client.get(f"/patients/{patients[0]['id']}")
        assert detail.status_code==200 and "hba1c" in detail.json()
        assert client.get("/patients/999999").status_code==404

def test_glucose_routes_and_unverified_forecast():
    with TestClient(app) as client:
        patient=client.get("/patients").json()[0]
        reading={"timestamp":"2026-01-01T00:00:00","glucose":112.5,"heart_rate":72,"activity":1.2,"mets":1.1}
        created=client.post(f"/patients/{patient['id']}/readings",json=reading)
        assert created.status_code==201
        assert client.get(f"/patients/{patient['id']}/readings").json()[-1]["glucose"]==112.5
        status=client.get("/predictions/status").json()
        assert status["checkpoint_loaded"] is True
        assert status["inference_ready"] is True
        forecast_readings=[{**reading,"timestamp":(datetime(2026,1,1)+timedelta(minutes=5*i)).isoformat()} for i in range(180)]
        forecast=client.post("/predictions/forecast",json={"patient_id":patient['id'],"readings":forecast_readings})
        assert forecast.status_code==200
        result=forecast.json()
        assert len(result["predictions"])==12
        assert result["spike_flag"] is (result["max_predicted_rise"]>=30)
        times=[datetime.fromisoformat(point["timestamp"]) for point in result["predictions"]]
        assert all(b-a==timedelta(minutes=5) for a,b in zip(times,times[1:]))
        replay=client.post("/simulation/replay",json={"patient_id":patient['id'],"subject_id":1,"limit":5})
        assert replay.status_code==200 and replay.json()["inserted"]==5
