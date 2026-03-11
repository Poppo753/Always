"""Watcher: aspetta che voice_transcription finisca, poi lancia image_analysis e il resto."""
import os
import sys
import time
import json
import subprocess
from pathlib import Path

ROOT = Path("D:/Documents/Projects/Ana/whatsapp-yearbook")
MANIFEST = ROOT / "runs/run_001/run_manifest.json"
AUDIO_CACHE = ROOT / "cache/audio"

env = os.environ.copy()
env["HF_HOME"] = "D:\\hf_cache"

CLI = [sys.executable, "-m", "yearbook.cli"]

print("Watcher avviato. Controllo ogni 60 secondi...", flush=True)

while True:
    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        done = m.get("completed_stages", [])
        cache_count = len(list(AUDIO_CACHE.rglob("*.json")))
        print(f"  [{time.strftime('%H:%M:%S')}] Audio in cache: {cache_count}/636  |  Done: {done}", flush=True)

        if "voice_transcription" in done:
            print("Voice transcription COMPLETATA!", flush=True)
            break
    except Exception as e:
        print(f"  Errore: {e}", flush=True)

    time.sleep(60)

# 1. image_analysis (force perche il manifest non lo ha come completato)
print("\nLancio image_analysis con Qwen 7B...", flush=True)
subprocess.run(
    CLI + ["run-stage", "image_analysis", "--root", str(ROOT), "--run-id", "run_001", "--force"],
    env=env, cwd=str(ROOT)
)
print("image_analysis completata!", flush=True)

# 2. run-all per completare (context_build, reasoning, summarize, render)
print("\nLancio run-all per finire il resto...", flush=True)
subprocess.run(
    CLI + ["run-all", "--root", str(ROOT), "--run-id", "run_001"],
    env=env, cwd=str(ROOT)
)

print("\nTUTTO COMPLETATO! PPTX pronto in output/", flush=True)
