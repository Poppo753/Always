import whisper
import os
import pandas as pd
from pathlib import Path
import subprocess
import time

# === CONFIG - HARDCODED PATHS ===
INPUT_FILE = r"C:\Users\loren\Downloads\otb_meeting.m4a"  # <-- Metti qui il percorso del tuo file
OUTPUT_CSV = r"D:\transcription_Otb.csv"  # <-- Metti qui dove salvare il CSV
MODEL = "large-v3"  # Modello Whisper (tiny, base, small, medium, large, large-v2, large-v3, large-v3-turbo)

# Converti in Path objects
INPUT_FILE = Path(INPUT_FILE)
OUTPUT_CSV = Path(OUTPUT_CSV)

# Crea la cartella di output se non esiste
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# Carica il modello Whisper su GPU
print("[INFO] Caricamento modello Whisper su GPU (CUDA)...")
model = whisper.load_model(MODEL, device="cuda")

# Verifica che il file di input esista
if not INPUT_FILE.exists():
    print(f"[ERRORE] File non trovato: {INPUT_FILE}")
    exit(1)

# Se il file CSV non esiste, lo crea con l'intestazione
if not OUTPUT_CSV.exists():
    pd.DataFrame(columns=["nome_file", "trascrizione"]).to_csv(OUTPUT_CSV, index=False)

# Statistiche per il report finale
audio_path = str(INPUT_FILE.with_suffix(".wav"))
print(f"[INFO] Elaborazione: {INPUT_FILE.name}")

start_time = time.time()

# Estrai l'audio dal video
print(f"[INFO] Estrazione audio da: {INPUT_FILE.name}")
cmd = [
    "ffmpeg", "-y", "-i", str(INPUT_FILE), 
    "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
]
try:
    subprocess.run(cmd, check=True, capture_output=True)
except Exception as e:
    print(f"[!] Errore nell'estrazione audio: {e}")
    exit(1)

# Trascrivi l'audio con Whisper
print(f"[INFO] Trascrizione in corso...")
try:
    result = model.transcribe(audio_path)
    transcription_text = result["text"]
    audio_duration = result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0
except Exception as e:
    print(f"[!] Errore nella trascrizione: {e}")
    transcription_text = "Errore nella trascrizione"
    audio_duration = 0

elapsed_time = time.time() - start_time

# Rimuovi il file audio temporaneo
try:
    os.remove(audio_path)
except Exception as e:
    print(f"[!] Errore nella rimozione del file audio: {e}")

# Aggiungi i dati al CSV
try:
    new_data = pd.DataFrame([[INPUT_FILE.stem, transcription_text]], columns=["nome_file", "trascrizione"])
    new_data.to_csv(OUTPUT_CSV, mode='a', header=False, index=False, encoding="utf-8")
    print(f"[OK] Trascrizione salvata per: {INPUT_FILE.name}")
    print(f"[STATS] Tempo elaborazione: {elapsed_time:.2f}s | Durata audio: {audio_duration:.2f}s | Velocità: {audio_duration/elapsed_time:.2f}x")
except Exception as e:
    print(f"[!] Errore nel salvataggio della trascrizione: {e}")
    exit(1)

print(f"\n{'='*60}")
print(f"[OK] Trascrizione completata e salvata in: {OUTPUT_CSV}")
print(f"\n📊 REPORT:")
print(f"{'='*60}")
print(f"File: {INPUT_FILE.name}")
print(f"Tempo elaborazione: {elapsed_time:.2f}s ({elapsed_time/60:.2f} minuti)")
print(f"Durata audio: {audio_duration:.2f}s ({audio_duration/60:.2f} minuti)")
print(f"Velocità: {audio_duration/elapsed_time:.2f}x tempo reale")
print(f"Tempo per secondo di audio: {elapsed_time/audio_duration:.3f}s" if audio_duration > 0 else "N/A")
print(f"{'='*60}")
