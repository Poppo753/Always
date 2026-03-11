
# AI_MODEL_SETUP.md

## Setup dei modelli AI per WhatsApp Yearbook Generator

Questo documento definisce **come installare e rendere disponibili i modelli AI necessari al progetto**.

Il sistema utilizza **tre modelli separati**:

| modello                | ruolo                           |
| ---------------------- | ------------------------------- |
| GPT-OSS-20B            | reasoning e scrittura narrativa |
| Qwen2.5-VL-7B-Instruct | analisi immagini                |
| Whisper                | trascrizione vocali             |

---

# 1. Architettura dei modelli

Pipeline logica:

```
images
↓
Qwen2.5-VL
↓
image captions / OCR / tags
↓
GPT-OSS
↓
daily reasoning
↓
daily summary
```

```
voice messages
↓
Whisper
↓
transcript
↓
GPT-OSS
```

---

# 2. GPT-OSS Setup (Ollama)

GPT-OSS viene eseguito tramite **Ollama**.

## Verifica installazione Ollama

```
ollama --version
```

Se non installato:

[https://ollama.com/download](https://ollama.com/download)

---

## Scaricare GPT-OSS

```
ollama pull gpt-oss:20b
```

---

## Verifica funzionamento

```
ollama run gpt-oss:20b
```

Se il modello risponde a un prompt, è correttamente installato.

---

## Come usarlo nel progetto

Il progetto dovrà chiamare Ollama tramite API locale.

Endpoint:

```
http://localhost:11434/api/generate
```

Esempio payload:

```json
{
  "model": "gpt-oss:20b",
  "prompt": "Explain this day summary",
  "stream": false
}
```

---

# 3. Qwen2.5-VL Setup (Vision Model)

Qwen2.5-VL viene usato tramite **HuggingFace Transformers**.

Non è gestito da Ollama.

---

# 4. Installare dipendenze Python

Nel virtual environment del progetto:

```
pip install git+https://github.com/huggingface/transformers accelerate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install qwen-vl-utils pillow
```

Queste librerie servono per:

| libreria      | scopo                     |
| ------------- | ------------------------- |
| transformers  | esecuzione modelli        |
| torch         | GPU inference             |
| qwen-vl-utils | parsing input multimodale |
| pillow        | gestione immagini         |

---

# 5. Scaricare Qwen2.5-VL

Creare file:

```
download_qwen.py
```

Contenuto:

```python
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

model_name = "Qwen/Qwen2.5-VL-7B-Instruct"

print("Downloading Qwen2.5-VL model...")

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_name,
    device_map="auto"
)

processor = AutoProcessor.from_pretrained(model_name)

print("Qwen2.5-VL downloaded successfully.")
```

---

## Eseguire download

```
python download_qwen.py
```

Il download richiede circa:

```
~15 GB
```

---

# 6. Dove viene salvato il modello

Transformers salva automaticamente i modelli nella cache locale.

### Windows

```
C:\Users\<USER>\.cache\huggingface
```

### Linux / WSL

```
~/.cache/huggingface
```

Cartella tipica:

```
models--Qwen--Qwen2.5-VL-7B-Instruct
```

---

# 7. Regole per l'uso nel progetto

Il modello **non deve essere caricato più volte**.

Caricarlo una sola volta all'avvio del processo.

Pattern consigliato:

```
global model
global processor
```

oppure singleton service.

---

# 8. Uso previsto nel progetto

Qwen2.5-VL viene utilizzato per:

* caption immagini
* classificazione scene
* rilevamento screenshot
* rilevamento testo (OCR leggero)
* valutazione rilevanza narrativa

Output previsto:

```json
{
  "short_caption": "cena sushi",
  "scene_category": "restaurant",
  "contains_text": false,
  "is_screenshot": false,
  "people_count_estimate": 2,
  "narrative_relevance_score": 0.82
}
```

---

# 9. Best practice GPU

Per GPU da **12GB VRAM**:

* analizzare **una immagine per volta**
* limitare `max_new_tokens`
* evitare batch grandi

Parametri consigliati:

```
torch_dtype="auto"
device_map="auto"
max_new_tokens=256
```

---

# 10. Test minimo Qwen

Dopo il download, test rapido:

```
python download_qwen.py
```

Se appare:

```
Qwen2.5-VL downloaded successfully.
```

il modello è pronto.

---

# 11. Stack finale del progetto

```
GPT-OSS (Ollama)
↓
reasoning e scrittura

Qwen2.5-VL
↓
analisi immagini

Whisper
↓
trascrizione vocali
```

---

# 12. Checklist finale

Prima di sviluppare il progetto assicurarsi che:

```
[✓] Ollama installato
[✓] GPT-OSS scaricato
[✓] dipendenze Python installate
[✓] Qwen2.5-VL scaricato
[✓] cache HuggingFace popolata
```

---

Se vuoi, nel prossimo passo posso anche scriverti **un secondo documento da dare a Codex** che spiega **come integrare Qwen e GPT-OSS nella pipeline del progetto**, così VSCode può generare direttamente i moduli Python corretti (`qwen_client.py`, `ollama_client.py`, ecc.).
