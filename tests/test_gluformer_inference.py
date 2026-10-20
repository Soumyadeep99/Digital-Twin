from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from app.services.gluformer import service


def test_spike_aware_checkpoint_on_held_out_cgmacros_subjects():
    archive_path = Path(__file__).resolve().parents[1] / "gluformer_cgmacros_subject_split.npz"
    archive = np.load(archive_path, allow_pickle=False)
    subjects = sorted({str(subject) for subject in archive["ID_test"]})
    assert service.model is not None, service.error
    assert service.compatibility_confirmed

    for subject_name in subjects:
        row = int(np.flatnonzero(archive["ID_test"] == subject_name)[0])
        subject_id = int(subject_name.rsplit("-", 1)[1])
        timestamps = archive["X_time_test"][row].astype("datetime64[ns]")
        readings = [
            SimpleNamespace(
                timestamp=datetime.fromisoformat(np.datetime_as_string(timestamp, unit="us")),
                glucose=float(glucose),
            )
            for timestamp, glucose in zip(timestamps, archive["X_test"][row])
        ]

        forecast = service.predict(readings, subject_id=subject_id)
        values = np.asarray([glucose for _, glucose in forecast])
        forecast_times = np.asarray([np.datetime64(timestamp, "us") for timestamp, _ in forecast])
        expected_times = archive["Y_time_test"][row].astype("datetime64[us]")
        rmse = np.sqrt(np.mean((values - archive["Y_test"][row]) ** 2))

        assert values.shape == (12,)
        assert np.isfinite(values).all()
        assert np.all((values >= 20) & (values <= 600))
        np.testing.assert_array_equal(forecast_times, expected_times)
        assert rmse < 30, f"{subject_name}: held-out forecast RMSE was {rmse:.2f} mg/dL"
