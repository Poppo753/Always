"""Benchmark: Qwen2.5-VL speed test with CUDA 12.8 / Blackwell."""
import json
import logging
import os
import time
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\hf_cache")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from yearbook.ai.qwen_vl_client import QwenVLClient

PROMPT = (
    "Describe this image as JSON: "
    '{"caption": "description", "category": "selfie|food|travel|other", "tags": []}'
)

img = Path("input/media/IMG-20230414-WA0014.jpg")
client = QwenVLClient(model_name="Qwen/Qwen2.5-VL-7B-Instruct")

# First call includes model loading
t0 = time.time()
r1 = client.analyze_image(img, PROMPT)
t1 = time.time()
print(f"1st image (includes model load): {t1-t0:.1f}s")

# Second call: pure inference
t2 = time.time()
r2 = client.analyze_image(img, PROMPT)
t3 = time.time()
print(f"2nd image (inference only):      {t3-t2:.1f}s")
print("Result:", r1)
