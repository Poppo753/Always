```markdown
# Feature Design Document
## WhatsApp AI Yearbook — Advanced Memory Features

Questo documento raccoglie **tutte le idee di feature avanzate** che rendono il progetto più di un semplice riassunto di chat.

L'obiettivo non è solo generare slide, ma creare un vero **AI Memory Engine** che trasformi una conversazione in una **storia narrativa della relazione**.

---

# 1. Emotional Timeline

## Descrizione

Costruire una **curva emotiva della relazione nel tempo**.

L'AI analizza tutti i messaggi per estrarre segnali emotivi e produce una timeline dell'intensità emotiva.

Esempio output:

```

Gen   ❤️
Feb   ❤️❤️
Mar   ❤️❤️❤️
Apr   💔
May   ❤️
Jun   ❤️❤️

```

Oppure grafico:

```

emotion
↑
|      ❤️❤️❤️
|   ❤️
|        ❤️❤️
| ❤️
+----------------------→
months

```

## Segnali utilizzati

- parole emotive
- emoji
- lunghezza messaggi
- vocali
- numero messaggi
- presenza foto

## Utilità

Permette di vedere **come evolve la relazione nel tempo**.

---

# 2. Moments That Defined The Year

## Descrizione

Il sistema trova automaticamente **i momenti più importanti dell'anno**.

Esempio:

```

⭐ Most intense day
14 July 2024
312 messages
6 photos
3 voice notes

```

## Eventi identificabili

- giorno con più messaggi
- giorno con più foto
- giorno con più vocali
- giorno più romantico
- giorno più divertente
- giorno più intenso

## Metodo

Utilizzare ranking basato su:

```

message_count
media_count
emotion_score
event_detection

```

---

# 3. AI Photo Curation

## Descrizione

Selezione automatica delle **foto migliori dell'anno**.

Non tutte le immagini vengono usate.

Il sistema seleziona:

```

Top 20 photos of the year

```

## Criteri

- qualità tecnica
- rilevanza narrativa
- presenza di persone
- connessione con eventi

## Output

Slide tipo:

```

Trip to Granada
June 2024

```

---

# 4. Memorable Quotes

## Descrizione

Il sistema estrae automaticamente **le frasi più significative della chat**.

Esempi:

```

"I can't wait to see you tonight"

```
```

"We should move in together"

```

## Metodo

Ranking messaggi basato su:

- intensità emotiva
- lunghezza
- posizione nel contesto
- risposta della controparte

## Output

Slide dedicate:

```

Quotes you'll remember

```

---

# 5. Automatic Movie Trailer

## Descrizione

Generazione automatica di un **video riassunto della relazione**.

Formato:

```

Your Year Together
2024

```

Durata suggerita:

```

60–90 seconds

```

## Contenuto

- immagini selezionate
- citazioni
- momenti chiave
- musica

## Struttura

```

Intro
↓
Highlights
↓
Emotional peak
↓
Ending

```

---

# 6. Conversation Map

## Descrizione

Visualizzazione della struttura della conversazione.

Esempio:

```

Lorenzo 52%
Marta   48%

```

Grafici possibili:

### Distribuzione messaggi

```

Messages
██████████
████████

```

### Tipo contenuto

```

text messages
photos
voice notes

```

---

# 7. Running Jokes Detection

## Descrizione

Identificare i **temi ricorrenti della chat**.

Esempio:

```

pizza
Netflix
gatto

```

Output:

```

Your most recurring topics

```

Metodo:

- keyword frequency
- clustering semantico
- LLM topic detection

---

# 8. Relationship Milestones

## Descrizione

Rilevazione automatica di **momenti simbolici della relazione**.

Possibili milestone:

```

first time you said "ti amo"
first trip
first fight
moving together

```

Metodo:

- keyword detection
- event clustering
- reasoning model

---

# 9. Daily Mood Classification

## Descrizione

Ogni giorno riceve un **mood principale**.

Possibili categorie:

```

😊 happy
😴 chill
🔥 intense
💔 conflict
🎉 celebration

```

Metodo:

analisi di:

- parole
- emoji
- tono conversazione
- eventi

---

# 10. Memory Prompts

## Descrizione

Alla fine del report vengono generate domande riflessive.

Esempio:

```

Questions about your year:

What was your favorite moment?
What surprised you the most?
What moment made you laugh the most?

```

Serve per stimolare **riflessione personale**.

---

# 11. Relationship Timeline

## Descrizione

Timeline dei momenti più importanti.

Esempio:

```

March 2023
First conversation

April 2023
First date

June 2023
Trip to Granada

October 2023
Period of distance

February 2024
Trip to Bormio

```

---

# 12. Emotional Peaks Detection

## Descrizione

Rilevazione dei giorni con **attività anomala**.

Tipico pattern:

```

normal day: 10 messages
special day: 200 messages

```

Metodo:

```

z-score detection
message density
media spikes

```

---

# 13. Memory Graph

## Descrizione

Costruzione di una rete di ricordi collegati.

Esempio:

```

Granada Trip
├ photos
├ messages
├ quotes
└ events

```

Questo crea una **mappa dei ricordi**.

---

# 14. Annual Relationship Report

## Descrizione

Report finale dell'anno.

Esempio:

```

Days talked: 341
Messages: 18,420
Photos shared: 612
Voice notes: 93

```

Momento più intenso:

```

14 July 2024
312 messages

```

---

# Struttura finale dell'output

Il progetto non genera solo slide giornaliere.

Struttura suggerita:

```

Part 1
Year overview

Part 2
Relationship timeline

Part 3
Important moments

Part 4
Daily highlights

Part 5
Photos

Part 6
Statistics

```

---

# Vision del progetto

Questo progetto diventa:

```

AI Memory Engine

```

non solo:

```

chat → summary

```

ma:

```

chat
↓
AI understands memories
↓
relationship narrative
↓
yearbook / video / timeline

```
```
