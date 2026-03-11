# System Architecture — WhatsApp Daily Yearbook Generator

## 1. Scopo del documento

Questo documento definisce la **System Architecture completa** del progetto **WhatsApp Daily Yearbook Generator**, cioè il sistema che trasforma una chat WhatsApp esportata con media in un **yearbook giornaliero** composto da una slide PowerPoint per ogni giorno di un anno.

Questo documento è pensato come **blueprint tecnico end-to-end** per costruire davvero il progetto, non come semplice overview. Include:

* architettura logica e fisica
* micro-pipeline
* orchestrazione multimodale
* queue processing
* caching e idempotenza
* modello dati
* componenti AI
* gestione errori
* performance target
* roadmap implementativa

---

## 2. Executive summary

L’architettura corretta del progetto non deve essere:

**chat raw → LLM → summary**

ma:

**ingestione → parsing → normalizzazione → arricchimento media → event detection → ranking → reasoning multimodale → generazione narrativa → rendering PowerPoint**

Il sistema deve essere progettato come una **pipeline modulare, cacheabile, ripetibile e parzialmente rigenerabile**, in modo da:

* evitare di ricalcolare tutto ogni volta
* permettere tuning dei prompt senza rifare OCR/STT
* gestire 365 giorni con costo computazionale sostenibile
* permettere debug per singolo giorno o singolo media asset

---

## 3. Principi architetturali

### 3.1 Modularity first

Ogni fase deve produrre artefatti intermedi persistiti su disco.

### 3.2 Reproducibility

A parità di input, config e seed, il sistema deve produrre risultati confrontabili.

### 3.3 Local-first privacy

Tutti i dati devono poter restare offline in locale.

### 3.4 Idempotent processing

Rilanciare una fase non deve rompere lo stato precedente.

### 3.5 Partial recomputation

Se cambia un prompt di summarization, non va rifatto OCR delle immagini.

### 3.6 Human-auditable outputs

Ogni output AI deve essere tracciabile alle sue sorgenti.

---

## 4. Livello di completezza del documento

Sì: questo, insieme al PRD funzionale precedente, è **sostanzialmente il documento completo** che può portare alla creazione dell’intero progetto.

Più precisamente:

* il **PRD** definisce **cosa** deve fare il sistema
* questa **System Architecture** definisce **come** costruirlo

Per arrivare allo sviluppo reale mancherebbero poi solo tre deliverable operativi:

1. **Technical Design Spec per modulo**
2. **Data contracts / schema JSON finali**
3. **piano implementativo sprint-by-sprint**

Quindi: non è ancora il codice, ma è già una base assolutamente seria per costruire il prodotto end-to-end.

---

## 5. High-level architecture

```text
WhatsApp Export
   ↓
Ingestion Layer
   ↓
Parsing & Normalization Layer
   ↓
Media Intelligence Layer
   ├─ Image Analysis (Qwen2.5-VL 7B — multimodal perception)
   ├─ OCR extraction (Qwen2.5-VL 7B)
   └─ Voice Transcription (Whisper large-v3)
   ↓
Event Detection Layer
   ↓
Ranking & Signal Extraction Layer
   ↓
Daily Context Builder
   ↓
GPT-OSS-20B Reasoning Layer
   ↓
Summary Generation (GPT-OSS-20B)
   ↓
PPTX Rendering Layer
   ↓
PowerPoint Yearbook
```

---

## 6. Logical component architecture

### 6.1 Input Gateway

Responsabile di acquisire e validare il pacchetto input.

Input attesi:

* `_chat.txt`
* cartella media
* file di configurazione progetto
* eventuali override utente

Responsabilità:

* validazione struttura cartelle
* controllo encoding file
* hashing file input
* creazione run manifest

Output:

* `run_manifest.json`
* `input_inventory.json`

---

### 6.2 Parser Service

Converte il file esportato WhatsApp in eventi strutturati.

Responsabilità:

* parsing date
* parsing autore messaggio
* parsing multilinea
* parsing placeholder allegati
* gestione system messages
* mappatura messaggio ↔ allegato

Output:

* `messages_raw.jsonl`
* `messages_normalized.parquet`

---

### 6.3 Media Registry

Indicizza tutti i media e li collega ai messaggi.

Responsabilità:

* inventario immagini/video/audio
* normalizzazione path
* inferenza estensione reale
* hash file per deduplica
* collegamento con timestamp messaggio

Output:

* `media_registry.json`

---

### 6.4 Image Intelligence Service

Analizza immagini collegate alla chat.

Tecnologia principale:

* **Qwen2.5-VL 7B**

Responsabilità:

* captioning
* OCR leggero/contestuale
* classificazione immagine (selfie, screenshot, food, travel, meme, doc, room, pet, ecc.)
* estrazione segnali visivi utili alla narrativa
* scoring rilevanza immagine

Nota: Qwen2.5-VL **non** esegue reasoning finale o generazione narrativa. Produce segnali strutturati che verranno consumati dal GPT-OSS-20B Reasoning Layer a valle.

Output:

* `image_analysis.jsonl`

---

### 6.5 Voice Intelligence Service

Trascrive vocali e produce metadati.

Tecnologia principale:

* **Whisper large-v3**

Responsabilità:

* trascrizione
* lingua
* durata
* confidence stimata
* summary opzionale del vocale

Output:

* `voice_transcripts.jsonl`

---

### 6.6 Event Detection Engine

Identifica eventi salienti all’interno della giornata.

Responsabilità:

* clustering temporale
* segmentazione conversazionale
* rilevazione burst activity
* rilevazione eventi media-driven
* rilevazione eventi emozionali
* tagging semantico evento

Output:

* `events.jsonl`

---

### 6.7 Ranking Engine

Calcola la rilevanza di messaggi, eventi, immagini e vocali.

Responsabilità:

* scoring messaggi
* scoring immagini
* scoring vocali
* scoring cluster
* selezione top-N per giorno

Output:

* `ranked_day_assets.jsonl`

---

### 6.8 Daily Context Builder

Costruisce il “pacchetto semantico del giorno”.

Responsabilità:

* aggregazione per data
* unione eventi + top messages + immagini + vocali
* statistiche del giorno
* metadata conversazione
* generazione contesto strutturato per LLM

Output:

* `daily_contexts/2024-05-12.json`

---

### 6.9 Multimodal Reasoning Service

Interpreta il giorno nel suo insieme.

Tecnologia principale:

* **GPT-OSS-20B**

Responsabilità:

* ricevere il contesto strutturato del giorno prodotto dalle fasi precedenti della pipeline
* identificare il tema della giornata
* distinguere evento importante da rumore
* inferire tono emotivo e classificare il mood
* identificare materiali da mostrare in slide
* produrre `daily_reasoning` strutturato

Nota: GPT-OSS-20B riceve caption immagini (da Qwen2.5-VL), trascrizioni vocali (da Whisper), eventi rilevati e messaggi ranked — non elabora direttamente i media.

Output:

* `daily_reasoning/2024-05-12.json`

---

### 6.10 Narrative Generation Service

Trasforma il reasoning strutturato in contenuti editoriali.

Modello:

* **GPT-OSS-20B** (stesso modello del reasoning layer, invocato con prompt di generazione narrativa)

Responsabilità:

* titolo del giorno
* summary breve/medio
* punti salienti
* quote del giorno
* mood
* note visuali per il renderer

Output:

* `daily_summaries/2024-05-12.json`

---

### 6.11 Presentation Renderer

Genera la slide PowerPoint.

Tecnologie:

* `python-pptx`
* `Pillow`

Responsabilità:

* layout
* collage immagini
* tipografia
* impaginazione contenuti
* generazione deck finale

Output:

* `yearbook_2024.pptx`
* preview PNG opzionali per slide

---

## 7. Physical architecture (single-machine local)

### 7.1 Target environment

Macchina locale Windows con GPU consumer NVIDIA (es. RTX 5070 12 GB).

### 7.2 Runtime architecture

```text
User Workspace
 ├─ Python application
 ├─ Local model runtime
 │   ├─ Qwen2.5-VL 7B  (multimodal perception)
 │   └─ Whisper large-v3 (audio transcription)
 ├─ GPT-OSS-20B client (reasoning & narrative generation)
 ├─ Disk cache
 ├─ Artifact store
 └─ Output renderer
```

### 7.3 Suggested execution stack

* Python 3.11+
* PyTorch
* Transformers
* Accelerate
* Pillow
* python-pptx
* pandas / pyarrow
* SQLite or DuckDB for metadata
* optional: vLLM / llama.cpp depending on chosen inference route

---

## 8. Micro-pipeline design

Il sistema deve essere suddiviso in **micro-pipeline riavviabili**.

### Pipeline A — Project bootstrap

Input:

* cartella input

Output:

* struttura progetto
* manifest run

Steps:

1. validate input
2. create run_id
3. snapshot config
4. inventory media

---

### Pipeline B — Chat parsing

Steps:

1. load `_chat.txt`
2. detect export pattern
3. parse messages
4. normalize timestamps
5. map attachments
6. persist output

---

### Pipeline C — Media enrichment

Sub-pipeline immagini:

1. load image file
2. compute hash
3. check cache
4. run Qwen2.5-VL analysis if cache miss
5. persist analysis

Sub-pipeline vocali:

1. load audio
2. compute hash
3. check cache
4. transcribe with Whisper if cache miss
5. persist transcript

---

### Pipeline D — Day grouping

Steps:

1. group messages by local date
2. attach media
3. compute day stats
4. write day bundle

---

### Pipeline E — Event detection

Steps:

1. build temporal clusters
2. classify cluster type
3. score cluster
4. emit event records

---

### Pipeline F — Ranking

Steps:

1. score each message
2. score each media asset
3. score each event
4. select best assets per day

---

### Pipeline G — Reasoning (GPT-OSS-20B)

Steps:

1. build compact structured context from daily_context
2. send context (top messages + image captions + voice transcripts + events + stats) to GPT-OSS-20B
3. infer day-level meaning, theme, mood
4. persist reasoning JSON

---

### Pipeline H — Narrative generation (GPT-OSS-20B)

Steps:

1. feed structured reasoning to GPT-OSS-20B
2. request title/summary/mood/quote/key_moments
3. validate JSON output
4. persist summary

---

### Pipeline I — Rendering

Steps:

1. select slide template
2. generate collage
3. place text blocks
4. export deck
5. export previews

---

## 9. Queue processing design

Anche se il sistema gira su una sola macchina, conviene progettare internamente una logica a code.

### 9.1 Perché usare queue semantics

Perché permettono:

* resumability
* parallelismo controllato
* retry di singoli task
* visibilità sullo stato del run

### 9.2 Queue abstraction consigliata

Per MVP locale:

* semplice coda in SQLite / DuckDB / file-based job registry

In seguito, se necessario:

* Celery / RQ / dramatiq

### 9.3 Job types

* `parse_chat`
* `analyze_image`
* `transcribe_voice`
* `build_day_context`
* `detect_day_events`
* `reason_day`
* `summarize_day`
* `render_day_slide`
* `render_deck`

### 9.4 Job schema

```json
{
  "job_id": "...",
  "job_type": "analyze_image",
  "entity_id": "IMG-20240512-WA0003.jpg",
  "status": "pending|running|done|failed",
  "attempt": 1,
  "priority": 5,
  "created_at": "...",
  "updated_at": "..."
}
```

### 9.5 Retry policy

* retry massimo: 2 o 3 tentativi
* backoff lineare o esponenziale leggero
* classificazione errori recoverable/non-recoverable

---

## 10. Caching strategy

Questo è uno dei punti più importanti di tutto il progetto.

### 10.1 Perché il caching è fondamentale

Senza caching ogni modifica al prompt costringerebbe a rifare:

* OCR immagini
* analisi caption
* trascrizione vocali
* reasoning giornaliero

### 10.2 Livelli di cache

#### Cache L1 — File hash cache

Chiave:

* SHA256 del file media

Usata per:

* immagini
* vocali
* video keyframes futuri

#### Cache L2 — Prompted inference cache

Chiave:

* hash(input_normalized + model_name + prompt_version + config)

Usata per:

* caption immagini
* reasoning giornaliero
* summary giornaliero

#### Cache L3 — Derived artifact cache

Chiave:

* hash(daily_summary + template_version)

Usata per:

* collage
* slide render

### 10.3 Cosa cachare

* image caption
* OCR extracted text
* image semantic tags
* voice transcript
* event detection outputs
* ranking outputs
* reasoning outputs
* summaries
* slide previews

### 10.4 Invalidation rules

Cache invalid se cambia:

* modello
* versione prompt
* versione parser
* configurazione scoring
* template renderer

---

## 11. Embeddings caching

Sì, ha senso anche una cache embeddings.

### 11.1 Use cases embeddings

* deduplica semantica messaggi
* similarità tra giorni
* identificazione pattern relazionali
* clustering conversazionale
* ricerca quote/temi ricorrenti

### 11.2 Cosa embedare

* messaggi significativi
* cluster di conversazione
* trascrizioni vocali
* caption immagini
* summary giornalieri

### 11.3 Storage

Per MVP:

* parquet + numpy arrays
  oppure
* SQLite con blob

Per versione avanzata:

* FAISS locale

### 11.4 Benefici pratici

* evitare selezione ridondante di messaggi quasi identici
* trovare giorni simili
* arricchire ranking
* preparare future feature annual highlights

---

## 12. Multimodal orchestration

Questo è il cuore del sistema.

### 12.1 Regola fondamentale

Il modello multimodale non deve ricevere tutto indiscriminatamente.

Deve ricevere un **pacchetto curato**.

### 12.2 Orchestration flow per singolo giorno

```text
Daily raw assets
   ↓
Event detector
   ↓
Ranking engine
   ↓
Selected assets package
   ├─ top messages
   ├─ top events
   ├─ top image captions (from Qwen2.5-VL)
   ├─ top voice transcripts (from Whisper)
   └─ daily stats
   ↓
GPT-OSS-20B Reasoning Layer
   ↓
Structured day interpretation (daily_reasoning)
   ↓
GPT-OSS-20B Narrative Generator
   ↓
daily_summary
```

### 12.3 Policy di selezione asset

Per esempio:

* max 12 messaggi ad alta rilevanza
* max 4 immagini
* max 2 estratti vocali
* max 6 eventi

### 12.4 Perché funziona meglio

Perché riduce:

* rumore
* dispersione di contesto
* allucinazioni narrative
* summary piatti e generici

---

## 13. AI model architecture

## 13.1 Primary VLM — Multimodal Perception

### Qwen2.5-VL 7B

Uso previsto:

* caption immagini
* OCR contestuale
* classificazione visiva (screenshot, meme, food, travel, ecc.)
* estrazione segnali visivi strutturati

Qwen2.5-VL **non** esegue reasoning finale, generazione narrativa, mood classification o summary. Produce dati strutturati (`image_analysis.jsonl`) consumati a valle dal reasoning layer.

Motivazioni:

* buon equilibrio qualità / fattibilità su 12 GB
* forte su screenshot e immagini con testo
* adatto a casi WhatsApp reali, non solo foto estetiche

---

## 13.2 Speech model

### Whisper large-v3

Uso previsto:

* trascrizione vocali
* language detection
* eventuale chunking per audio lunghi
* short summary opzionale del vocale

---

## 13.3 Reasoning & Narrative Generation model

### GPT-OSS-20B

Uso previsto:

* daily interpretation: riceve il contesto strutturato del giorno (messaggi ranked, caption immagini, trascrizioni vocali, eventi rilevati, statistiche)
* theme detection
* mood classification
* title generation
* summary generation
* key moment synthesis
* quote selection

Produce:

* `daily_reasoning` (interpretazione strutturata del giorno)
* `daily_summary` (contenuto narrativo per la slide)

GPT-OSS-20B è il motore di ragionamento centrale della pipeline. Riceve dati già elaborati dalle fasi percettive (Qwen2.5-VL, Whisper) e dalla pipeline di event detection / ranking, e produce l'output semantico finale.

---

## 14. Data architecture

### 14.1 Directory layout suggerito

```text
project_root/
├── input/
│   ├── _chat.txt
│   └── media/
├── runs/
│   └── run_2026_03_10_001/
│       ├── manifest/
│       ├── parsed/
│       ├── registry/
│       ├── analysis/
│       ├── events/
│       ├── ranking/
│       ├── daily_contexts/
│       ├── reasoning/
│       ├── summaries/
│       ├── collages/
│       ├── slides/
│       └── output/
├── cache/
│   ├── images/
│   ├── audio/
│   ├── reasoning/
│   └── embeddings/
├── templates/
├── config/
└── logs/
```

### 14.2 Storage format recommendations

* JSONL per output iterabili e grandi
* Parquet per dataset tabellari
* PNG/JPG per preview
* PPTX finale per output utente

---

## 15. Data contracts principali

### 15.1 Message record

```json
{
  "message_id": "msg_000001",
  "timestamp": "2024-05-12T19:01:00",
  "date": "2024-05-12",
  "sender": "Lorenzo",
  "message_type": "image",
  "text": null,
  "attachment": "IMG-20240512-WA0003.jpg",
  "reply_to": null,
  "is_system": false
}
```

### 15.2 Image analysis record

```json
{
  "media_id": "img_000123",
  "filename": "IMG-20240512-WA0003.jpg",
  "sha256": "...",
  "caption": "due piatti sushi su tavolo di ristorante",
  "category": "food_restaurant",
  "ocr_text": "",
  "relevance_score": 0.84,
  "analysis_version": "qwen25vl7b_v1"
}
```

### 15.3 Daily summary record

```json
{
  "date": "2024-05-12",
  "title": "Cena sushi e messaggi affettuosi",
  "summary": "Giornata tranquilla culminata in una cena condivisa...",
  "key_moments": [
    "Organizzazione della serata",
    "Foto al ristorante",
    "Scambio affettuoso a fine giornata"
  ],
  "quote": "Non vedo l'ora di vederti",
  "mood": "warm_playful",
  "selected_images": ["IMG-20240512-WA0003.jpg"],
  "stats": {
    "message_count": 82,
    "image_count": 3,
    "voice_count": 1
  }
}
```

---

## 16. Event detection design

### 16.1 Event categories

* `conversation_burst`
* `image_shared`
* `voice_shared`
* `planning`
* `emotion_peak`
* `good_morning_routine`
* `good_night_closure`
* `outing_meal`
* `travel_signal`
* `conflict_signal`
* `silence_gap`

### 16.2 Event scoring dimensions

* temporal density
* semantic intensity
* media association
* emotional intensity
* novelty relative to nearby events

### 16.3 Event generation algorithm (conceptual)

1. segment messages into temporal windows
2. detect conversational clusters
3. identify triggers (image, long voice, emotional keywords, planning phrases)
4. collapse related triggers into event candidates
5. assign event type and confidence

---

## 17. Ranking engine design

### 17.1 Message scoring formula

Indicativa:

`score = length_weight + emotional_weight + reply_centrality + media_proximity + novelty + semantic_salience`

### 17.2 Image scoring formula

`score = caption_relevance + social_context + uniqueness + non_blurriness_proxy + event_attachment_bonus`

### 17.3 Voice scoring formula

`score = duration_band + transcript_salience + emotional_keywords + event_link_bonus`

### 17.4 Anti-noise heuristics

Penalizzare:

* messaggi monosillabici isolati
* sticker non descrivibili
* screenshot duplicati
* immagini identiche o quasi identiche

---

## 18. Prompt architecture

### 18.1 Prompt versioning

Ogni prompt deve avere:

* `prompt_name`
* `prompt_version`
* `model_name`
* `temperature`
* `schema_version`

### 18.2 Prompt families

* image_caption_prompt (Qwen2.5-VL 7B)
* voice_transcription_prompt (Whisper large-v3)
* day_reasoning_prompt (GPT-OSS-20B)
* day_summary_prompt (GPT-OSS-20B)
* quote_selection_prompt (GPT-OSS-20B)
* mood_classification_prompt (GPT-OSS-20B)

### 18.3 Output constraints

Tutti gli output AI devono essere richiesti in **JSON strutturato** con validazione successiva.

---

## 19. Validation layer

### 19.1 Perché serve

Gli LLM possono:

* restituire JSON rotto
* inventare quote
* produrre campi mancanti
* eccedere la lunghezza desiderata

### 19.2 Validation rules

* schema JSON obbligatorio
* quote solo da testi effettivamente presenti
* selected_images ⊆ immagini reali del giorno
* mood appartenente a set finito
* max lengths per campo

### 19.3 Recovery strategy

Se fallisce la validazione:

1. retry con prompt repair
2. fallback a versione più semplice del prompt
3. se ancora fallisce, generazione minimale rule-based

---

## 20. Rendering architecture

### 20.1 Rendering model

Il renderer non deve ragionare: deve solo impaginare.

### 20.2 Input renderer

* daily summary JSON
* selected image files
* template config

### 20.3 Slide regions

* header: data + titolo
* left body: riassunto + key moments
* right body: collage foto
* footer: quote + stats + mood

### 20.4 Template versioning

Permettere più temi futuri:

* romantic
* minimal
* documentary
* scrapbook

---

## 21. Observability and logging

### 21.1 Log levels

* INFO
* WARNING
* ERROR
* DEBUG

### 21.2 Cosa loggare

* tempo per fase
* cache hit/miss
* numero media processati
* errori per file
* giorni saltati
* giorni con summary incompleto

### 21.3 Run report finale

Generare un `run_report.json` con:

* totale messaggi
* totale giorni
* immagini analizzate
* vocali trascritti
* cache hit ratio
* tempo totale
* warning principali

---

## 22. Error handling strategy

### Errori recoverable

* JSON invalido da modello
* timeout immagine singola
* OCR vuoto
* audio troppo rumoroso

### Errori non-recoverable

* `_chat.txt` mancante
* encoding illeggibile non risolvibile
* nessuna data parsabile
* output directory non scrivibile

### Policy

* fallire “gracefully” a livello di singolo asset
* non bloccare l’intero run per un media corrotto

---

## 23. Performance architecture

### 23.1 Performance target MVP

* ingestione: < 1 min
* parsing chat: pochi secondi
* analisi immagini: principale collo di bottiglia
* trascrizione vocali: collo di bottiglia secondario
* rendering deck: veloce

### 23.2 Ottimizzazioni principali

* cache aggressiva
* batch per immagini quando possibile
* pre-scaling immagini troppo grandi
* limitazione top-N assets per giorno
* parallelismo moderato CPU-side per preparazione dati

---

## 24. Security and privacy

### 24.1 Principi

* local-only by default
* nessun invio dati esterno
* path sanitization
* log senza contenuti sensibili estesi

### 24.2 Modalità privacy opzionali

* anonimizzazione nomi
* quote ridotte
* esclusione giorni sensibili
* blur o esclusione immagini specifiche

---

## 25. Recommended MVP implementation order

### Sprint 1

* parser chat
* media registry
* daily grouping

### Sprint 2

* image analysis con Qwen2.5-VL 7B
* voice transcription con Whisper
* cache file-based

### Sprint 3

* event detection
* ranking engine
* daily context builder

### Sprint 4

* day reasoning
* narrative generation
* validation layer

### Sprint 5

* PowerPoint renderer
* collage builder
* report finale

### Sprint 6

* queue system leggero
* resume from checkpoint
* profiling e tuning

---

## 26. Future architecture extensions

* supporto video con keyframe extraction
* DOCX renderer parallelo
* highlights mensili e annuali
* search semantica nel dataset chat
* UI desktop/web locale
* human review loop per correggere singole giornate
* scoring personalizzato user-defined

---

## 27. Final assessment

### Questa architettura è sufficiente per costruire il progetto intero?

**Sì, sostanzialmente sì.**

Con il PRD funzionale e questa System Architecture hai già:

* visione di prodotto
* componenti tecnici
* pipeline completa
* modelli AI consigliati
* strategia di caching
* orchestrazione multimodale
* struttura dati
* piano implementativo

### Cosa manca per partire davvero con il coding?

Solo documenti di livello ancora più operativo:

* schema JSON definitivo per ogni file
* specifiche modulo-per-modulo
* task breakdown di implementazione

In altre parole:

**questo è già un blueprint serio da cui un developer può partire davvero.**

---

## 28. Prossimo documento consigliato

Il passo successivo più utile è uno di questi due:

1. **Technical Design Specification completa modulo per modulo**
2. **Project skeleton reale** con cartelle, file Python, interfacce, classi e pipeline stub

Per trasformare tutto questo in codice, il documento più utile è il punto 2.
