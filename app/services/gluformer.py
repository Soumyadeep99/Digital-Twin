"""Inference for the supplied CGMacros Gluformer checkpoint.

Architecture and preprocessing follow the published Gluformer HF implementation
(`njeffrie/Gluformer`, modeling_gluformer.py and config.json). The local checkpoint
matches its tensor layout and sinusoidal positional embeddings. No model is trained here.
"""
import math
import os
from datetime import timedelta
from pathlib import Path

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]


class PositionalEmbedding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        position = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
        div_term = (torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model)).exp()
        embedding = torch.zeros(max_len, d_model)
        embedding[:, 0::2] = torch.sin(position * div_term)
        embedding[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pos_emb", embedding.unsqueeze(0))

    def forward(self, x):
        return self.pos_emb[:, :x.size(1)]


class TokenEmbedding(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.conv = nn.Conv1d(1, d_model, kernel_size=3, padding=1, padding_mode="circular")

    def forward(self, x):
        return self.conv(x.transpose(-1, 1)).transpose(-1, 1)


class TemporalEmbedding(nn.Module):
    def __init__(self, d_model: int, num_features: int):
        super().__init__()
        self.embed = nn.Linear(num_features, d_model)

    def forward(self, x):
        return self.embed(x.float())


class SubjectEmbedding(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.id_embedding = nn.Linear(1, d_model)

    def forward(self, subject_id):
        return self.id_embedding(subject_id.float().reshape(-1, 1))


class DataEmbedding(nn.Module):
    def __init__(self, d_model: int, num_features: int):
        super().__init__()
        self.value_embedding = TokenEmbedding(d_model)
        self.time_embedding = TemporalEmbedding(d_model, num_features)
        self.positional_embedding = PositionalEmbedding(d_model)
        self.subject_embedding = SubjectEmbedding(d_model)
        self.dropout = nn.Dropout(0.1)

    def forward(self, subject_id, values, time_features):
        values = self.value_embedding(values)
        values = values + self.positional_embedding(values) + self.time_embedding(time_features)
        subject = self.subject_embedding(subject_id).unsqueeze(1)
        return self.dropout(torch.cat((subject, values), dim=1))


class MultiheadAttention(nn.Module):
    def __init__(self, d_model: int, n_heads: int, d_keys: int, causal: bool):
        super().__init__()
        self.h, self.d, self.mask_flag = n_heads, d_keys, causal
        self.proj_q = nn.Linear(d_model, n_heads * d_keys)
        self.proj_k = nn.Linear(d_model, n_heads * d_keys)
        self.proj_v = nn.Linear(d_model, n_heads * d_keys)
        self.proj_out = nn.Linear(n_heads * d_keys, d_model)
        self.dropout = nn.Dropout(0.1)

    def forward(self, q, k, v):
        batch, q_len = q.shape[:2]
        k_len = k.shape[1]
        q, k, v = [layer(x).reshape(batch, -1, self.h, self.d) for layer, x in ((self.proj_q, q), (self.proj_k, k), (self.proj_v, v))]
        scores = torch.einsum("bnhd,bmhd->bhnm", (q, k)) / math.sqrt(self.d)
        if self.mask_flag:
            mask = torch.triu(torch.ones(q_len, k_len, dtype=torch.bool, device=q.device), diagonal=1)
            scores = scores.masked_fill(mask, -torch.inf)
        weights = self.dropout(torch.softmax(scores, dim=-1))
        output = torch.einsum("bhnm,bmhd->bnhd", (weights, v)).reshape(batch, q_len, self.h * self.d)
        return self.proj_out(output)


class EncoderLayer(nn.Module):
    def __init__(self, d_model: int, d_fcn: int, n_heads: int, d_keys: int):
        super().__init__()
        self.att = MultiheadAttention(d_model, n_heads, d_keys, causal=False)
        self.conv1 = nn.Conv1d(d_model, d_fcn, kernel_size=1)
        self.conv2 = nn.Conv1d(d_fcn, d_model, kernel_size=1)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x):
        x = self.norm1(x + self.dropout(self.att(x, x, x)))
        residual = self.dropout(F.gelu(self.conv1(x.transpose(-1, 1))))
        residual = self.dropout(self.conv2(residual).transpose(-1, 1))
        return self.norm2(x + residual)


class ConvLayer(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.downConv = nn.Conv1d(d_model, d_model, kernel_size=3, padding=1, padding_mode="circular")
        self.norm = nn.BatchNorm1d(d_model)
        self.activ = nn.ELU()
        self.maxPool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)

    def forward(self, x):
        x = self.activ(self.norm(self.downConv(x.transpose(-1, 1))))
        return self.maxPool(x).transpose(-1, 1)


class Encoder(nn.Module):
    def __init__(self, d_model: int, d_fcn: int, n_heads: int, d_keys: int):
        super().__init__()
        self.enc_layers = nn.ModuleList([EncoderLayer(d_model, d_fcn, n_heads, d_keys) for _ in range(2)])
        self.conv_layers = nn.ModuleList([ConvLayer(d_model)])
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x):
        x = self.enc_layers[0](x)
        x = self.conv_layers[0](x)
        x = self.enc_layers[-1](x)
        return self.norm(x)


class DecoderLayer(nn.Module):
    def __init__(self, d_model: int, d_fcn: int, n_heads: int, d_keys: int):
        super().__init__()
        self.self_att = MultiheadAttention(d_model, n_heads, d_keys, causal=True)
        self.cross_att = MultiheadAttention(d_model, n_heads, d_keys, causal=False)
        self.conv1 = nn.Conv1d(d_model, d_fcn, kernel_size=1)
        self.conv2 = nn.Conv1d(d_fcn, d_model, kernel_size=1)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x, memory):
        x = self.norm1(x + self.self_att(x, x, x))
        x = self.norm2(x + self.cross_att(x, memory, memory))
        residual = self.dropout(F.gelu(self.conv1(x.transpose(-1, 1))))
        residual = self.dropout(self.conv2(residual).transpose(-1, 1))
        return self.norm3(x + residual)


class Decoder(nn.Module):
    def __init__(self, d_model: int, d_fcn: int, n_heads: int, d_keys: int):
        super().__init__()
        self.layers = nn.ModuleList([DecoderLayer(d_model, d_fcn, n_heads, d_keys)])
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, memory):
        for layer in self.layers:
            x = layer(x, memory)
        return self.norm(x)


class Variance(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.proj1 = nn.Linear(d_model, 1)
        self.dropout = nn.Dropout(0.1)
        self.activ1 = nn.ReLU()
        self.proj2 = nn.Linear(181, 1)
        self.activ2 = nn.Tanh()

    def forward(self, x):
        x = self.dropout(self.activ1(self.proj1(x))).transpose(-1, -2)
        return 10 * self.activ2(self.proj2(x))


class ForecastModel(nn.Module):
    # These dimensions are confirmed by the published config and checkpoint tensor shapes.
    def __init__(self):
        super().__init__()
        d_model, n_heads, d_fcn = 512, 12, 2048
        d_keys = d_model // n_heads
        self.enc_embedding = DataEmbedding(d_model, 5)
        self.dec_embedding = DataEmbedding(d_model, 5)
        self.encoder = Encoder(d_model, d_fcn, n_heads, d_keys)
        self.decoder = Decoder(d_model, d_fcn, n_heads, d_keys)
        self.projection = nn.Linear(d_model, 1)
        self.var = Variance(d_model)

    def forward(self, subject_id, x, x_time, decoder, decoder_time):
        embedded = self.enc_embedding(subject_id, x, x_time)
        variance = self.var(embedded)
        memory = self.encoder(embedded)
        output = self.decoder(self.dec_embedding(subject_id, decoder, decoder_time), memory)
        return self.projection(output)[:, -12:, :], variance


class GluFormer(nn.Module):
    """Checkpoint root module, matching GluformerForTimeSeries.model."""
    def __init__(self):
        super().__init__()
        self.model = ForecastModel()

    def forward(self, *args):
        return self.model(*args)


class GluFormerService:
    LOWER, UPPER = 38.0, 402.0
    LABEL_LENGTH, PREDICTION_LENGTH = 60, 12

    def __init__(self):
        self.path = Path(os.getenv("GLUFORMER_CHECKPOINT", str(ROOT / "checkpoints" / "best_gluformer_spike_aware.pt")))
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.error = None
        self.compatibility_confirmed = False
        if self.path.exists():
            try:
                payload = torch.load(self.path, map_location="cpu", weights_only=True)
                state = payload.get("model_state_dict", payload)
                self.model = GluFormer()
                self.model.load_state_dict(state, strict=True)
                self.model.to(self.device).eval()
                # Exact checkpoint key/shape loading against the published source config
                # is validated by tests/test_gluformer_inference.py on held-out CGMacros.
                self.compatibility_confirmed = True
            except Exception as exc:
                self.model = None
                self.error = f"Checkpoint architecture could not be loaded: {exc}"
        else:
            self.error = f"Checkpoint not found: {self.path}"

    @classmethod
    def normalize_glucose(cls, values):
        return (values - cls.LOWER) / (cls.UPPER - cls.LOWER) * 10.0 - 5.0

    @classmethod
    def unnormalize_glucose(cls, values):
        return (values + 5.0) / 10.0 * (cls.UPPER - cls.LOWER) + cls.LOWER

    @staticmethod
    def _time_features(stamps):
        values = np.asarray(stamps, dtype="datetime64[ns]")
        day = values.astype("datetime64[D]")
        year = values.astype("datetime64[Y]")
        month = values.astype("datetime64[M]")
        hour = values.astype("datetime64[h]")
        return np.stack((
            ((day - year).astype("timedelta64[D]").astype(np.int64) + 1) / 182.5 - 1.0,
            ((day - month).astype("timedelta64[D]").astype(np.int64) + 1) / 15.5 - 1.0,
            ((day.astype(np.int64) + 3) % 7) / 3.5 - 1.0,
            (hour - day).astype("timedelta64[h]").astype(np.int64) / 12.0 - 1.0,
            (values.astype("datetime64[m]") - hour).astype("timedelta64[m]").astype(np.int64) / 30.0 - 1.0,
        ), axis=-1).astype(np.float32)

    @staticmethod
    def _to_numpy_timestamp(stamp):
        # Match the source preprocessor's naive datetime64 timestamps. Aware input is normalized to UTC.
        if stamp.tzinfo is not None:
            from datetime import timezone
            stamp = stamp.astimezone(timezone.utc).replace(tzinfo=None)
        return np.datetime64(stamp, "ns")

    def predict(self, readings, subject_id=1):
        if self.model is None:
            raise RuntimeError(self.error or "GluFormer is unavailable")
        readings = sorted(readings, key=lambda reading: reading.timestamp)
        if len(readings) != 180:
            raise ValueError("Exactly 180 readings are required")
        times = [reading.timestamp for reading in readings]
        from datetime import timezone
        normalized_times = [stamp.astimezone(timezone.utc).replace(tzinfo=None) if stamp.tzinfo else stamp for stamp in times]
        for earlier, later in zip(normalized_times, normalized_times[1:]):
            if later - earlier != timedelta(minutes=5):
                raise ValueError("Readings must be exactly five minutes apart")
        raw = np.asarray([reading.glucose for reading in readings], dtype=np.float32)
        if not np.isfinite(raw).all() or np.any((raw < 20) | (raw > 600)):
            raise ValueError("Glucose readings must be finite values between 20 and 600 mg/dL")
        stamps = np.asarray([self._to_numpy_timestamp(stamp) for stamp in times], dtype="datetime64[ns]")
        future = [normalized_times[-1] + timedelta(minutes=5 * step) for step in range(1, self.PREDICTION_LENGTH + 1)]
        decoder_values = np.concatenate((self.normalize_glucose(raw[-self.LABEL_LENGTH:]), np.zeros(self.PREDICTION_LENGTH, dtype=np.float32)))
        decoder_times = np.asarray([self._to_numpy_timestamp(stamp) for stamp in normalized_times[-self.LABEL_LENGTH:] + future], dtype="datetime64[ns]")
        x = torch.from_numpy(self.normalize_glucose(raw).reshape(1, 180, 1).astype(np.float32)).to(self.device)
        x_time = torch.from_numpy(self._time_features(stamps)[None, :, :]).to(self.device)
        decoder = torch.from_numpy(decoder_values.reshape(1, 72, 1)).to(self.device)
        decoder_time = torch.from_numpy(self._time_features(decoder_times)[None, :, :]).to(self.device)
        subject = torch.tensor([float(subject_id)], dtype=torch.float32, device=self.device)
        with torch.inference_mode():
            normalized_prediction, _ = self.model(subject, x, x_time, decoder, decoder_time)
        values = self.unnormalize_glucose(normalized_prediction[0, :, 0].float().cpu().numpy())
        if values.shape != (12,) or not np.isfinite(values).all():
            raise RuntimeError("GluFormer returned invalid forecast values")
        if np.any((values < 20) | (values > 600)):
            raise RuntimeError("GluFormer returned out-of-range glucose values")
        return [(future[index], float(values[index])) for index in range(12)]


service = GluFormerService()
