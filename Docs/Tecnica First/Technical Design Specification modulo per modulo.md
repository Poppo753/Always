
# 3. Technical Design Specification modulo per modulo

## 3.1 Ingestion Module

### Obiettivo

Validare l’input e creare il contesto di run.

### Input

* `input/_chat.txt`
* `input/media/`
* config YAML

### Output

* `run_manifest.json`
* inventory iniziale media

### Classi

* `InputValidator`
* `InventoryBuilder`
* `BootstrapService`

### Regole

* fallire subito se `_chat.txt` manca
* warning se cartella media manca
* creare sempre una snapshot config per il run

---

## 3.2 Parsing Module

### Obiettivo

Convertire l’export WhatsApp in record strutturati.

### Classi

* `WhatsAppParser`
* `AttachmentMatcher`
* `MessageNormalizer`

### Algoritmo

1. leggere file come testo UTF-8 con fallback controllato
2. identificare righe che iniziano un nuovo messaggio
3. unire righe multilinea
4. estrarre timestamp, sender e corpo
5. rilevare allegati placeholder
6. assegnare `message_type`
7. creare `message_id`

### Edge cases

* messaggi multilinea
* messaggi di sistema
* timestamp con formati leggermente diversi
* allegati mancanti su disco

### Test essenziali

* parsing chat piccola
* parsing chat multilinea
* parsing chat con immagini e vocali

---

## 3.3 Media Registry Module

### Obiettivo

Creare indice unico di tutti i media.

### Classi

* `MediaRegistryBuilder`

### Algoritmo

1. enumerare file in `input/media`
2. calcolare SHA256
3. inferire MIME e tipo media
4. collegare media ai messaggi per filename
5. marcare duplicati tramite hash

### Test essenziali

* immagini duplicate
* file con estensione inconsistente
* allegato menzionato ma assente

---

## 3.4 Image Analysis Module

### Obiettivo

Analizzare immagini con Qwen2.5-VL 7B per estrarre segnali percettivi strutturati.

### Classi

* `QwenVLClient`
* `ImageAnalyzer`
* `ImageScorer`

### Input

* record media immagine
* prompt di captioning

### Output

* `image_analysis_record`

### Prompt requirements

Il prompt deve chiedere:

* descrizione sintetica
* tipo scena
* presenza testo
* utilità narrativa
* eventuali warning

Nota: Qwen2.5-VL produce **solo dati percettivi** (caption, OCR, classificazione, scoring). Non esegue reasoning finale, generazione narrativa o mood classification. Questi compiti sono delegati a GPT-OSS-20B.

### Cache

Chiave:

* hash immagine + prompt_version + model_name

### Test essenziali

* foto normale
* screenshot con testo
* meme
* immagine vuota o corrotta

---

## 3.5 Voice Transcription Module

### Obiettivo

Trascrivere vocali con Whisper.

### Classi

* `WhisperClient`
* `VoiceTranscriber`

### Algoritmo

1. caricare audio
2. trascrivere
3. estrarre lingua
4. creare short summary opzionale
5. salvare output

### Cache

Chiave:

* hash audio + model_name

### Test essenziali

* vocale breve pulito
* vocale rumoroso
* file audio corrotto

---

## 3.6 Day Grouping Module

### Obiettivo

Raggruppare tutti i contenuti per giorno.

### Classi

* `DayGrouper`
* `StatsBuilder`

### Algoritmo

1. filtrare per anno target
2. group by `date`
3. allegare media e analisi
4. calcolare statistiche del giorno

### Output

* day bundle grezzo

---

## 3.7 Event Detection Module

### Obiettivo

Individuare eventi significativi nel giorno.

### Classi

* `TemporalClusterer`
* `EventDetector`
* `EventClassifier`
* `EventScorer`

### Algoritmo

1. creare cluster temporali di messaggi
2. rilevare trigger semantici
3. collegare media
4. classificare il tipo di evento
5. assegnare score e confidence

### Heuristics iniziali

* gap temporale per nuovo cluster: configurabile, es. 30-60 minuti
* bonus a cluster con immagini o vocali
* bonus a frasi emotive o di pianificazione

---

## 3.8 Ranking Module

### Obiettivo

Selezionare il sottoinsieme migliore di segnali da dare al reasoning.

### Classi

* `MessageRanker`
* `VoiceRanker`
* `DayAssetRanker`
* `AntiNoiseFilter`

### Strategie

* scoring per messaggi, eventi, immagini, vocali
* limiti top-N
* deduplica semantica semplice

### Configurazione

Tutti i pesi devono stare in `config/ranking.yaml`

---

## 3.9 Context Builder Module

### Obiettivo

Costruire il contesto strutturato del giorno.

### Classi

* `DailyContextBuilder`
* `QuoteSelector`

### Regole

* il contesto deve essere compatto
* niente raw dump dell’intera chat
* includere solo evidenze utili
* includere candidate quote solo se realmente presenti

---

## 3.10 Reasoning Module

### Obiettivo

Interpretare il giorno con **GPT-OSS-20B**.

### Classi

* `GptOssClient`
* `DayReasoner`
* `MoodClassifier`
* `SignalInterpreter`

### Input

* `daily_context` (contesto strutturato prodotto dalle fasi precedenti della pipeline)
* caption immagini (da Qwen2.5-VL)
* trascrizioni vocali (da Whisper)
* eventi rilevati
* messaggi ranked

### Output

* `daily_reasoning`

### Regole

* output JSON obbligatorio
* le affermazioni devono essere sostenute da `evidence`
* non inventare eventi non presenti
* GPT-OSS-20B riceve solo dati già strutturati, non media raw

---

## 3.11 Summary Generation Module

### Obiettivo

Trasformare il reasoning in testo leggibile da slide.

### Modello

**GPT-OSS-20B** (stesso modello del reasoning layer, invocato con prompt di generazione narrativa)

### Classi

* `NarrativeGenerator`
* `SummaryPostprocessor`
* `FactualGuard`

### Input

* `daily_reasoning` (output di GPT-OSS-20B reasoning layer)

### Regole di stile

* titolo breve e umano
* summary di 2-4 frasi
* key moments massimo 3-4
* quote breve e reale
* testo non troppo ripetitivo tra giorni

### Validazioni

* quote deve corrispondere a un messaggio reale
* selected images devono essere subset valido

---

## 3.12 Rendering Module

### Obiettivo

Generare la presentazione finale.

### Classi

* `PptxRenderer`
* `CollageBuilder`
* `SlideLayoutEngine`
* `PreviewExporter`

### Algoritmo slide

1. aprire template
2. creare una slide per giorno
3. inserire data e titolo
4. inserire summary e bullet momenti
5. generare collage immagini
6. inserire quote e stats
7. esportare deck finale

### Regole di layout

* evitare overflow testo
* fallback se nessuna immagine disponibile
* limite testo per area

---

## 3.13 Validation Module

### Obiettivo

Garantire coerenza dei contratti dati e degli output AI.

### Classi

* `JsonSchemaValidator`
* `ContractChecks`
* `InputSanityChecks`

### Checks principali

* schema compliance
* riferimenti a ID esistenti
* lunghezze testo
* consistenza selected assets

---

## 3.14 Reporting Module

### Obiettivo

Produrre diagnostica finale di run.

### Classi

* `RunReportBuilder`
* `DiagnosticsCollector`

### Output

* `run_report.json`
* eventuale report markdown leggibile

---
