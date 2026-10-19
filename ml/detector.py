"""ONNX adapter for the published Community Forensics v13 image detector."""

import hashlib
import io
import os

import numpy as np
import onnxruntime as ort
from django.conf import settings
from PIL import Image, ImageOps


EXPECTED_SHA256 = "6ca91ded511f0cfbf3ded2a7b76e37f62273c42cb42c303b1faf4933c53beeef"
MODEL_ID = "angelhd25/ull-ai-image-detector@88ae192e4001bcbbf6f02de75e033171e227b5b2"
MEAN = np.array([0.48145466, 0.4578275, 0.40821073], np.float32)
STD = np.array([0.26862954, 0.26130258, 0.27577711], np.float32)


def prepare(raw: bytes) -> np.ndarray:
    with Image.open(io.BytesIO(raw)) as source:
        source.load()
        oriented = ImageOps.exif_transpose(source)
        if oriented.mode in {"RGBA", "LA"} or "transparency" in oriented.info:
            rgba = oriented.convert("RGBA")
            white = Image.new("RGBA", rgba.size, "white")
            white.alpha_composite(rgba)
            image = white.convert("RGB")
        else:
            image = oriented.convert("RGB")
        width, height = image.size
        scale = 440 / min(width, height)
        image = image.resize((round(width * scale), round(height * scale)), Image.Resampling.BICUBIC)
        width, height = image.size
        left, top = (width - 384) // 2, (height - 384) // 2
        image = image.crop((left, top, left + 384, top + 384))
        return ((np.asarray(image, np.float32) / 255.0 - MEAN) / STD).transpose(2, 0, 1)[None]


class Detector:
    def __init__(self):
        path = settings.MODEL_PATH
        if not path.exists():
            raise FileNotFoundError("Файл модели отсутствует. Выполните download_model.")
        self.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        if self.sha256 != EXPECTED_SHA256:
            raise ValueError("Контрольная сумма модели не совпадает с опубликованной.")
        providers = ["CPUExecutionProvider"]
        if os.getenv("PHOTOTRACE_DEVICE", "CPU").upper() == "CUDA" and "CUDAExecutionProvider" in ort.get_available_providers():
            providers.insert(0, "CUDAExecutionProvider")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        self.session = ort.InferenceSession(str(path), sess_options=options, providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, raw: bytes) -> float:
        tensor = prepare(raw)
        logit = float(self.session.run(None, {self.input_name: tensor})[0].reshape(-1)[0])
        # Numerically stable sigmoid. This is a model score until independent calibration.
        return float(np.exp(-np.logaddexp(0, -logit)))


def verdict_for_score(score: float) -> str:
    # Provisional thresholds; validation data must replace them for the final study.
    if score <= 0.35:
        return "likely_real"
    if score >= 0.65:
        return "likely_generated"
    return "uncertain"
