import whisper
import os
import pandas as pd
from pathlib import Path
import subprocess
import time

# === CONFIG - HARDCODED PATHS ===
INPUT_FOLDER = r"C:\Users\loren\Downloads\output-20260205T205239Z-3-001\output"  # <-- Cartella con i file da trascrivere
OUTPUT_FOLDER = r"D:\transcriptions"  # <-- Cartella dove salvare i CSV
MODEL = "large-v3"  # Modello Whisper (tiny, base, small, medium, large, large-v2, large-v3, large-v3-turbo)

# Estensioni file supportate
SUPPORTED_EXTENSIONS = ['.m4a', '.mp4', '.mp3', '.wav', '.avi', '.mkv', '.mov', '.flv', '.webm']

# Converti in Path objects
INPUT_FOLDER = Path(INPUT_FOLDER)
OUTPUT_FOLDER = Path(OUTPUT_FOLDER)

# Crea la cartella di output se non esiste
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Verifica che la cartella di input esista
if not INPUT_FOLDER.exists():
    print(f"[ERRORE] Cartella non trovata: {INPUT_FOLDER}")
    exit(1)

# Trova tutti i file nella cartella di input
input_files = [f for f in INPUT_FOLDER.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

if not input_files:
    print(f"[ERRORE] Nessun file supportato trovato in: {INPUT_FOLDER}")
    print(f"[INFO] Estensioni supportate: {', '.join(SUPPORTED_EXTENSIONS)}")
    exit(1)

print(f"[INFO] Trovati {len(input_files)} file da elaborare")

# Carica il modello Whisper su GPU
print("[INFO] Caricamento modello Whisper su GPU (CUDA)...")
model = whisper.load_model(MODEL, device="cuda")

# Statistiche globali
total_start_time = time.time()
total_audio_duration = 0
processed_files = 0

# Processa ogni file
for INPUT_FILE in input_files:
    # Genera il nome del CSV di output basato sul nome del file
    OUTPUT_CSV = OUTPUT_FOLDER / f"transcription_{INPUT_FILE.stem}.csv"
    
    # Se il file CSV non esiste, lo crea con l'intestazione
    if not OUTPUT_CSV.exists():
        pd.DataFrame(columns=["nome_file", "trascrizione"]).to_csv(OUTPUT_CSV, index=False)
    
    # Statistiche per il singolo file
    audio_path = str(INPUT_FILE.parent / f"{INPUT_FILE.stem}_temp.wav")
    print(f"\n[INFO] Elaborazione ({processed_files + 1}/{len(input_files)}): {INPUT_FILE.name}")
    
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
        continue
    
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
        print(f"[OK] Trascrizione salvata in: {OUTPUT_CSV.name}")
        print(f"[STATS] Tempo: {elapsed_time:.2f}s | Durata: {audio_duration:.2f}s | Velocità: {audio_duration/elapsed_time:.2f}x")
        
        total_audio_duration += audio_duration
        processed_files += 1
    except Exception as e:
        print(f"[!] Errore nel salvataggio della trascrizione: {e}")
        continue

total_elapsed_time = time.time() - total_start_time

print(f"\n{'='*60}")
print(f"[OK] Elaborazione completata!")
print(f"\n📊 REPORT FINALE:")
print(f"{'='*60}")
print(f"File processati: {processed_files}/{len(input_files)}")
print(f"Tempo totale: {total_elapsed_time:.2f}s ({total_elapsed_time/60:.2f} minuti)")
print(f"Durata audio totale: {total_audio_duration:.2f}s ({total_audio_duration/60:.2f} minuti)")
print(f"Velocità media: {total_audio_duration/total_elapsed_time:.2f}x tempo reale" if total_elapsed_time > 0 else "N/A")
print(f"Output salvato in: {OUTPUT_FOLDER}")
print(f"{'='*60}")
