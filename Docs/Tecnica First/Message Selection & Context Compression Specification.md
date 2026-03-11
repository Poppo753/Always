
# Message Selection & Context Compression Specification

## Production-Grade Version

---

# 1. Scopo

Definire un sistema robusto per trasformare una conversazione giornaliera WhatsApp composta da:

```
50–500+ messaggi
```

in un contesto compatto per reasoning AI composto da:

```
10–25 messaggi
+
eventi
+
media
+
segnali semantici
```

senza perdere:

* il significato della conversazione
* il flusso dialogico
* i momenti narrativi importanti.

---

# 2. Principio architetturale fondamentale

Il sistema **non seleziona messaggi isolati**.

Il sistema seleziona:

```
conversation clusters
```

e poi estrae da essi **micro-dialoghi coerenti**.

---

# 3. Pipeline completa

Pipeline definitiva:

```
messages_of_day
↓
noise_filter
↓
temporal_clustering
↓
semantic_signal_detection
↓
media_proximity_scoring
↓
message_scoring
↓
cluster_scoring
↓
top_cluster_selection
↓
context_expansion
↓
message_extraction
↓
quote_detection
↓
context_packaging
```

---

# 4. Step 1 — Noise Filtering

## Obiettivo

Rimuovere messaggi privi di valore informativo.

## Regole

Un messaggio è **noise candidate** se:

```
word_count < 3
AND
not emoji meaningful
AND
not near media
```

### Esempi noise

```
ok
ahah
👍
😂
si
no
.
```

## Eccezioni

NON rimuovere se:

```
message_distance_from_media < 2
```

oppure se il messaggio appartiene a cluster attivo.

---

# 5. Step 2 — Temporal Clustering

## Obiettivo

Segmentare la conversazione in **burst conversazionali**.

### Algoritmo

```
if time_gap_between_messages > CLUSTER_GAP
    start_new_cluster
```

### Parametro

```
CLUSTER_GAP = 30–60 minutes
```

Configurabile.

---

## Esempio

```
18:30 Stasera sushi?
18:31 Sì
18:32 Dove?
18:33 Prenoto

→ cluster A

21:10 Guarda dove sono
21:10 IMG_1234.jpg
21:11 Bellissimo

→ cluster B
```

---

# 6. Step 3 — Semantic Signal Detection

Ogni messaggio riceve punteggi semantici.

### Tipi di segnali

#### Emotional signals

```
mi manchi
ti amo
non vedo l'ora
bellissimo
```

#### Planning signals

```
andiamo
vediamoci
stasera
domani
prenoto
```

#### Narrative signals

```
successo
indovina
ti racconto
non ci crederai
```

#### Reaction signals

```
❤️
😍
🥹
```

---

# 7. Step 4 — Media Proximity Scoring

Messaggi vicini a media hanno peso maggiore.

```
distance_from_media <= 2 messages
```

### Bonus

```
image_bonus = +0.3
voice_bonus = +0.25
video_bonus = +0.2
```

Motivo:

Media spesso rappresentano **momenti della giornata**.

---

# 8. Step 5 — Message Importance Score

Formula consigliata:

```
importance_score =
  semantic_score * 0.35
+ media_proximity * 0.25
+ message_length_score * 0.15
+ reply_depth_score * 0.15
+ emotional_signal_score * 0.10
```

### Range

```
0.0 – 1.0
```

---

# 9. Step 6 — Cluster Importance Score

Cluster rappresentano micro-storie.

Formula:

```
cluster_score =
  average(message_scores)
+ media_presence_bonus
+ event_overlap_bonus
+ message_density_bonus
```

### Media bonus

```
image_present → +0.2
voice_present → +0.15
```

---

# 10. Step 7 — Top Cluster Selection

Selezionare i cluster più rilevanti.

### Parametri consigliati

```
MAX_CLUSTERS = 3–5
```

Se giornata con:

```
>150 messaggi
```

aumentare a:

```
MAX_CLUSTERS = 6
```

---

# 11. Step 8 — Context Expansion (CRITICAL)

Questa è la parte che evita perdita di senso.

Quando un messaggio è selezionato:

```
msg_i
```

espandere contesto:

```
msg_(i-1)
msg_i
msg_(i+1)
```

se esistono.

---

## Regole

```
expansion_window = 1–2 messages
```

oppure fino a:

```
cluster_boundary
```

---

## Esempio

Chat:

```
Stasera sushi?
Sì dai
Dove?
Quello in centro
Prenoto
```

Messaggio selezionato:

```
Stasera sushi?
```

Context expansion produce:

```
Stasera sushi?
Sì dai
Dove?
```

---

# 12. Step 9 — Message Extraction

Da ogni cluster selezionato:

```
1–3 messaggi chiave
```

con contesto espanso.

### Limiti consigliati

```
MAX_MESSAGES_PER_CLUSTER = 5
TOTAL_MESSAGES_PER_DAY = 10–25
```

---

# 13. Step 10 — Quote Detection

Obiettivo: trovare frasi citabili.

### Regole

Una frase è candidata se:

```
5 ≤ word_count ≤ 15
emotion_signal present
sentence complete
not purely logistical
```

### Esempi

```
"Non vedo l'ora di vederti."
"Questa giornata è stata assurda."
"Ti racconto tutto stasera."
```

### Limite

```
MAX_QUOTES = 3
```

---

# 14. Step 11 — Context Packaging

Il reasoning model riceve:

```
DAY STATS
- message_count
- image_count
- voice_count

TOP EVENTS
- ...

CONVERSATION CLUSTERS
Cluster 1
Cluster 2
Cluster 3

TOP IMAGES
- caption

VOICE SUMMARIES
- ...

CANDIDATE QUOTES
```

---

# 15. Token Budget

GPT-OSS input raccomandato:

```
600–1200 tokens
```

Distribuzione ideale:

```
clusters          45%
events            15%
images            20%
voices            10%
stats             10%
```

---

# 16. Edge Case Handling

## Giorno con pochi messaggi

```
<15 messages
```

Passare **tutti i messaggi**.

---

## Giorno con solo immagini

Costruire cluster basati su media.

---

## Giorno dominato da vocali

Usare:

```
voice_transcript_summary
```

come messaggi principali.

---

# 17. Failure Modes

### Modello produce summary generico

Cause:

```
clusters troppo grandi
rumore non filtrato
```

---

### Perdita narrativa

Cause:

```
mancanza context expansion
```

---

### Quote inventate

Prevenzione:

```
quote must reference message_id
```

---

# 18. Metrics di qualità

Monitorare:

```
compression_ratio
cluster_coherence
quote_validity
summary_consistency
```

Compression ratio target:

```
10:1 – 20:1
```

---

# 19. Benefici dell’architettura

Questo sistema produce:

```
micro-storie della giornata
```

invece di:

```
messaggi casuali
```

Risultato:

* migliori riassunti
* titoli più naturali
* quote migliori
* slide più coerenti.

---

# 20. Decisione architetturale finale

Il reasoning model **non riceve mai la chat completa**.

Riceve una **conversazione compressa ma coerente** basata su:

```
temporal clustering
semantic scoring
media proximity
context expansion
cluster extraction
```
