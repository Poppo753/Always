Di seguito trovi un **PRD completo** per il progetto. È scritto come documento tecnico reale che potresti usare per sviluppare o condividere il progetto.

---

# PRD — WhatsApp Daily Yearbook Generator

## 1. Overview

### Nome progetto

**WhatsApp Daily Yearbook Generator**

### Descrizione

Sistema software che analizza una chat WhatsApp (testo, immagini, vocali) e genera automaticamente **una slide PowerPoint per ogni giorno di un anno**, contenente:

* titolo della giornata
* riassunto narrativo
* momenti principali
* citazione significativa
* collage di immagini
* statistiche della giornata
* mood della conversazione

L’obiettivo è produrre un **yearbook visivo e narrativo della relazione o conversazione**.

---

# 2. Obiettivi

## Obiettivo principale

Trasformare una chat WhatsApp in una **narrazione giorno per giorno** con supporto multimodale (testo + immagini + audio).

## Obiettivi secondari

* estrazione automatica eventi
* ranking dei momenti significativi
* comprensione immagini e screenshot
* trascrizione vocali
* generazione narrativa coerente
* output visuale elegante (PowerPoint)

---

# 3. Utente target

Utente tecnico o semi-tecnico che:

* ha accesso alla chat export
* possiede GPU consumer
* vuole generare un archivio narrativo della relazione.

---

# 4. Input dati

## Input primari

Export WhatsApp con media:

```
_chat.txt
IMG-xxxx.jpg
VID-xxxx.mp4
PTT-xxxx.opus
```

Formato standard export WhatsApp.

---

## Struttura messaggi esempio

```
[12/05/2024, 18:32] Lorenzo: Arrivo tra poco
[12/05/2024, 18:34] Marta: Ok
[12/05/2024, 19:01] Marta: <allegato: IMG-20240512-WA0003.jpg>
```

---

# 5. Output

## Output principale

PowerPoint:

```
yearbook_2024.pptx
```

### Slide layout

Slide per giorno:

```
----------------------------------
DATA

Titolo giornata

Riassunto narrativo

Momenti principali
• ...
• ...

Citazione del giorno

Collage immagini

Statistiche
----------------------------------
```

---

# 6. Architettura del sistema

Pipeline generale:

```
data ingestion
↓
chat parser
↓
media registry
↓
image analysis (Qwen2.5-VL 7B)
↓
voice transcription (Whisper large-v3)
↓
event detection
↓
ranking
↓
daily context builder
↓
GPT-OSS-20B reasoning layer
↓
summary generation (GPT-OSS-20B)
↓
PPTX rendering
```

---

# 7. Componenti del sistema

## 7.1 Chat Parser

### Funzione

Convertire `_chat.txt` in struttura dati analizzabile.

### Tecnologia

Python

Librerie:

* regex
* pandas
* pydantic

---

### Output

```
messages.json
```

Struttura:

```json
{
 "timestamp": "",
 "sender": "",
 "text": "",
 "message_type": "text|image|video|voice",
 "attachment": ""
}
```

---

# 7.2 Media Extraction

Estrazione media associati ai messaggi.

Struttura:

```
media_index.json
```

```json
{
 "IMG-001.jpg": {
  "timestamp": "...",
  "sender": "...",
  "message_id": "..."
 }
}
```

---

# 8. Media Analysis

## 8.1 Image Analysis

### Modello

**Qwen2.5-VL 7B**

Motivazioni:

* multimodal reasoning
* forte OCR
* screenshot understanding
* buona performance su GPU consumer

---

### Task

* caption immagini
* OCR
* detection screenshot
* detection meme
* detection scene

---

### Output

```
image_analysis.json
```

```json
{
 "image": "IMG-001.jpg",
 "caption": "foto a ristorante",
 "objects": ["food","restaurant"],
 "text_detected": "",
 "confidence": 0.88
}
```

---

## 8.2 Voice Transcription

### Modello

**Whisper large-v3**

Task:

* speech to text
* language detection

Output:

```
voice_transcripts.json
```

---

# 9. Event Detection

## Scopo

Trasformare la chat in **eventi semantici**.

---

## Tipologie eventi

| evento         | descrizione          |
| -------------- | -------------------- |
| conversation   | blocco conversazione |
| image_event    | invio foto           |
| voice_event    | vocale lungo         |
| plan_event     | pianificazione       |
| emotion_event  | messaggi emotivi     |
| activity_event | attività             |

---

## Algoritmo

1. clustering temporale messaggi
2. analisi contenuto
3. rilevamento media
4. scoring evento

---

### Output

```
events.json
```

```json
{
 "date": "2024-05-12",
 "events": [
  {
   "type": "image_event",
   "time": "19:01",
   "description": "foto ristorante"
  }
 ]
}
```

---

# 10. Content Ranking

Obiettivo: selezionare contenuti importanti.

---

## Scoring formula

Score =

```
message_length_weight
+ emotion_weight
+ proximity_to_media
+ conversation_cluster_weight
+ novelty_score
```

---

## Output

```
ranked_messages.json
```

---

# 11. Multimodal Reasoning

Input al modello:

```
top messages
event list
image captions
voice transcripts
daily statistics
```

---

## Modello

**GPT-OSS-20B**

Task:

* interpretare il contesto strutturato della giornata
* identificare il tema principale
* classificare il mood della conversazione
* selezionare momenti chiave e citazioni
* produrre `daily_reasoning`

Nota: Qwen2.5-VL 7B produce le caption e l'analisi visuale a monte; GPT-OSS-20B riceve il contesto già strutturato e svolge il ragionamento finale.

---

# 12. Narrative Generation

## Modello

**GPT-OSS-20B**

Generazione testo narrativo a partire dal `daily_reasoning` prodotto nella fase precedente.

Input:

```
daily_reasoning (output GPT-OSS-20B reasoning layer)
```

Output:

```json
{
 "title": "",
 "summary": "",
 "moments": [],
 "quote": "",
 "mood": ""
}
```

---

## Mood detection

Categorie:

* romantic
* neutral
* playful
* stressed
* nostalgic

---

# 13. Slide Generator

Tecnologia:

```
python-pptx
```

---

## Collage immagini

Tecnologia:

```
Pillow
```

Algoritmo:

* selezione top immagini
* grid layout
* dimension scaling

---

# 14. Struttura progetto

```
whatsapp_yearbook/

input/
 chat_export/
 media/

data/
 parsed/
 events/
 analysis/

models/

src/
 parser/
 media_analysis/
 event_detection/
 ranking/
 summarizer/
 ppt_generator/

output/
 pptx/
 previews/

templates/
 ppt_template.pptx
```

---

# 15. Modelli AI utilizzati

| componente              | modello          |
| ----------------------- | ---------------- |
| multimodal perception   | Qwen2.5-VL 7B   |
| speech recognition      | Whisper large-v3 |
| reasoning & generation  | GPT-OSS-20B     |

### Separazione responsabilità

* **Qwen2.5-VL 7B** → percezione multimodale (image captioning, OCR, classificazione visiva, estrazione segnali visivi)
* **Whisper large-v3** → trascrizione audio (voice message transcription e short summary)
* **GPT-OSS-20B** → ragionamento e generazione narrativa (daily interpretation, theme detection, mood classification, title generation, summary generation, key moment synthesis)

---

# 16. Hardware target

GPU:

RTX 5070 12GB

---

### VRAM stimata

| componente     | VRAM   |
| -------------- | ------ |
| Qwen2.5-VL 7B | ~10GB  |
| Whisper        | ~2GB   |
| GPT-OSS-20B    | API / separato |

---

# 17. Performance target

Processing time per giorno:

~2-5 secondi

Processing 365 giorni:

~30-40 minuti.

---

# 18. Prompt Design

Prompt reasoning esempio (GPT-OSS-20B):

```
You are the reasoning engine for a WhatsApp yearbook generator.
You receive a structured daily context produced by earlier pipeline stages
(chat parsing, image analysis via Qwen2.5-VL, voice transcription via Whisper).

DAILY CONTEXT:
...

EVENTS:
...

TOP MESSAGES:
...

IMAGE CAPTIONS:
...

VOICE TRANSCRIPTS:
...

Return a JSON with:
main_theme
day_type
importance_level
mood
reasoning_summary
evidence
selected_quote_message_id
selected_image_media_ids
```

---

# 19. MVP Scope

MVP include:

* parsing chat
* caption immagini
* event detection
* ranking messaggi
* daily summary
* generazione PowerPoint

---

# 20. Future Features

### highlights annuali

top 20 giorni.

---

### timeline mensile

slide riepilogo mese.

---

### emotion analytics

grafico andamento relazione.

---

### miglioramento immagini

AI upscaling.

---

# 21. Rischi

| rischio            | mitigazione      |
| ------------------ | ---------------- |
| OCR error          | fallback caption |
| chat rumorosa      | ranking          |
| immagini duplicate | dedup            |

---

# 22. Metriche qualità

* coerenza narrativa
* correttezza eventi
* qualità caption immagini
* leggibilità slide.

---

# 23. Roadmap sviluppo

### Phase 1

parser chat.

### Phase 2

media analysis.

### Phase 3

event detection.

### Phase 4

summary generation.

### Phase 5

PowerPoint rendering.

---

# 24. Stack tecnologico

Linguaggio:

Python

---

Framework:

* transformers
* pytorch
* python-pptx
* pillow
* pandas

---

Inference:

* vLLM
* llama.cpp (quantized)

---

# 25. Deployment

Locale.

---

# 26. Privacy

Tutti i dati rimangono:

* offline
* local machine

---

# Conclusione

Questo sistema permette di trasformare una chat WhatsApp in un **archivio narrativo giornaliero multimodale**, combinando:

* NLP
* vision models
* speech recognition
* generazione documenti.