# WhatsApp AI Yearbook — Feature Ranking

> Tutte le idee raccolte da 3 documenti + conversazione, classificate per **figata**, **utilità** e **effort**.
> Stato: ✅ fatto | 🔜 prossimo | 💡 futuro | ❌ scartato

---

## Legenda

| Colonna | Scala |
|---------|-------|
| **Figata** | ⭐⭐⭐ = wow virale · ⭐⭐ = bello · ⭐ = nice to have |
| **Utilità** | 🔥🔥🔥 = cambia tutto · 🔥🔥 = migliora · 🔥 = cosmetico |
| **Effort** | 🟢 < 1h · 🟡 1-4h · 🔴 4h+ |

---

## TIER S — Implementate

| # | Feature | Figata | Utilità | Effort | Stato |
|---|---------|--------|---------|--------|-------|
| 1 | **Video Analysis** (frame extraction + Whisper audio + narrative) | ⭐⭐⭐ | 🔥🔥🔥 | 🔴 | ✅ Fatto |
| 2 | **Video Thumbnails nel PPTX** (best aesthetic frame per video) | ⭐⭐ | 🔥🔥 | 🟡 | ✅ Fatto |
| 3 | **Stickers inclusi nell'analisi** (71 .webp) | ⭐ | 🔥🔥 | 🟢 | ✅ Fatto |
| 4 | **All-years support** (year_target: null) | ⭐ | 🔥🔥🔥 | 🟢 | ✅ Fatto |

---

## TIER 1 — Prossime (confermate dall'utente)

| # | Feature | Figata | Utilità | Effort | Fonte | Note |
|---|---------|--------|---------|--------|-------|------|
| 5 | **Face Clustering** | ⭐⭐⭐ | 🔥🔥🔥 | 🔴 | Doc1 #5 | `insightface` o `facenet-pytorch` + DBSCAN. "Persona A appare in 47 foto, A+B insieme in 23". Molto interessato. Da fare subito dopo pipeline. |
| 6 | **Cover Page + Stats Page** | ⭐⭐⭐ | 🔥🔥🔥 | 🟡 | Doc1 #2, Doc2 #14 | Copertina con migliore foto + titolo. Pagina stats: totale messaggi, foto, audio, giorni, giorno più intenso. Confermato "do after". |
| 7 | **Monthly Recap Slides** | ⭐⭐ | 🔥🔥 | 🟡 | Doc1 #8 | Best photo del mese, frase migliore, stats → struttura yearbook più leggibile. Confermato. |
| 8 | **HTML Export** | ⭐⭐ | 🔥🔥 | 🟡 | Doc1 #9, Doc3 | HTML statico con immagini embedded base64 → condivisibile su mobile. Interessato. |

---

## TIER 2 — Alta figata, effort medio-alto

| # | Feature | Figata | Utilità | Effort | Fonte | Note |
|---|---------|--------|---------|--------|-------|------|
| 9 | **Relationship Intelligence / Emotional Timeline** | ⭐⭐⭐ | 🔥🔥🔥 | 🔴 | Doc2 #1, Doc3 | LA killer feature. Curva emotiva della relazione nel tempo. Usa emoji, lunghezza msg, vocali, foto. "Spotify Wrapped della relazione". Richiede meta-analysis su event_records + daily_summaries che GIÀ generiamo. |
| 10 | **Moments That Defined The Year** | ⭐⭐⭐ | 🔥🔥🔥 | 🟡 | Doc2 #2 | Top moments automatici: giorno più messaggi, più foto, più romantico, più divertente. Ranking basato su message_count + media_count + emotion_score. Dati già disponibili dal ranking stage. |
| 11 | **Relationship Milestones Detection** | ⭐⭐⭐ | 🔥🔥 | 🔴 | Doc2 #8 | Primo "ti amo", primo viaggio, prima litigata, riconciliazione. Keyword detection + event clustering + LLM reasoning. |
| 12 | **Memorable Quotes / Smart Quotes** | ⭐⭐ | 🔥🔥 | 🟡 | Doc1 #12, Doc2 #4 | Cercare messaggi con pattern emotivi ("ti amo", "non ci credo", "finalmente") + brevi + non banali. Ranking per intensità emotiva × brevità × risposta controparte. |
| 13 | **AI Photo Curation — Top 20 dell'anno** | ⭐⭐⭐ | 🔥🔥 | 🟡 | Doc2 #3 | Selezione automatica migliori 20 foto basata su qualità tecnica + rilevanza narrativa + presenza persone. Qwen VL già dà aesthetic_score. |
| 14 | **Chapter-based Narrative** | ⭐⭐⭐ | 🔥🔥🔥 | 🔴 | Doc3 | "The Story of Us" con capitoli: The Beginning, Falling in Love, Our First Trip, Growing Together. GPT-OSS genera struttura narrativa dai daily summaries. Output molto "virale". |

---

## TIER 3 — Nice to have

| # | Feature | Figata | Utilità | Effort | Fonte | Note |
|---|---------|--------|---------|--------|-------|------|
| 15 | **Daily Mood Classification** | ⭐⭐ | 🔥 | 🟡 | Doc2 #9 | Ogni giorno → mood: 😊 happy, 😴 chill, 🔥 intense, 💔 conflict, 🎉 celebration. Input per emotional timeline. |
| 16 | **Conversation Map / Stats** | ⭐⭐ | 🔥 | 🟡 | Doc2 #6 | Chi scrive di più, distribuzione contenuti (text/photo/voice), percentuali. Parzialmente coperto da stats page (#6). |
| 17 | **Running Jokes / Topic Detection** | ⭐⭐ | 🔥 | 🟡 | Doc2 #7 | Temi ricorrenti: keyword frequency + clustering semantico + LLM. "Your most recurring topics". |
| 18 | **Memory Prompts** | ⭐ | 🔥 | 🟢 | Doc2 #10 | Domande riflessive a fine report: "What was your favorite moment?", "What surprised you the most?" GPT-OSS le genera facilmente. |
| 19 | **Emotional Peaks Detection** | ⭐⭐ | 🔥🔥 | 🟡 | Doc2 #12 | Z-score detection su message density e media spikes. Giorno normale: 10 msg, giorno speciale: 200 msg. Utile come input per #10 e #9. |
| 20 | **Relationship Timeline Slide** | ⭐⭐ | 🔥🔥 | 🟡 | Doc2 #11 | Timeline visiva: Mar 2023 → First conversation, Apr → First date, Jun → Trip, etc. Richiede milestone detection (#11). |
| 21 | **Word Cloud per Mese** | ⭐ | 🔥 | 🟡 | Doc1 #11 | Parole più usate per mese → tile visiva nel PPTX. `wordcloud` library. |

---

## TIER 4 — Scartate o rimandate

| # | Feature | Motivo | Fonte |
|---|---------|--------|-------|
| 22 | **Documenti OCR** | Troppo personali, solo 8 file | Doc1 #3 — Utente: "skip" |
| 23 | **Sentiment/Tone objettivo** | Troppo freddo/oggettivo per un regalo | Doc1 #6 — Utente: "skip" |
| 24 | **Event Clustering Multi-Giorno** | Complesso, beneficio limitato | Doc1 #7 — Utente: "skip" |
| 25 | **Location Parsing** | WhatsApp coords rare, poco impatto | Doc1 #10 — Utente: "skip" |
| 26 | **Lingua Italiana** | Output resta in inglese per scelta | Doc1 #1 — Utente: "keep English" |

---

## TIER 🚀 — Vision / Startup

| # | Feature | Figata | Descrizione | Fonte |
|---|---------|--------|-------------|-------|
| 27 | **Automatic Movie Trailer** | ⭐⭐⭐ | Video 60-90s con foto, citazioni, momenti chiave, musica. Intro → Highlights → Emotional Peak → Ending. | Doc2 #5 |
| 28 | **Memory Graph** | ⭐⭐⭐ | Rete di ricordi collegati: `Granada Trip ├ photos ├ messages ├ quotes └ events`. Mappa navigabile dei ricordi. | Doc2 #13 |
| 29 | **AI Memory Engine** | ⭐⭐⭐ | Visione completa: `chat → AI understands memories → relationship narrative → yearbook / video / timeline`. Non più "chat → summary" ma "relationship intelligence". | Doc2 vision, Doc3 |

---

## Roadmap Suggerita

### Fase 1 — Ora (pipeline finisce)
```
✅ Video Analysis + Thumbnails
✅ Stickers + All years
→  Pipeline completa → PPTX con foto reali
```

### Fase 2 — Subito dopo
```
#5  Face Clustering          🔴 4h+    ← user "very very interested"
#6  Cover + Stats Page       🟡 2h
#10 Moments That Defined     🟡 2h     ← dati già disponibili
#12 Smart Quotes             🟡 1-2h
```

### Fase 3 — Iterazione successiva
```
#7  Monthly Recap            🟡 2-3h
#13 AI Photo Curation Top20  🟡 2h
#9  Emotional Timeline       🔴 4h+    ← LA killer feature
#14 Chapter Narrative         🔴 4h+
```

### Fase 4 — Polish
```
#8  HTML Export              🟡 3h
#15 Daily Mood              🟡 1-2h
#11 Milestones Detection    🔴 4h+
#20 Relationship Timeline   🟡 2h (dopo #11)
```

### Fase 5 — Se diventa prodotto
```
#27 Movie Trailer           🔴 8h+
#28 Memory Graph            🔴 8h+
#29 AI Memory Engine        🔴 forever
```

---

## Dipendenze tra feature

```
#15 Daily Mood ──────┐
                     ├──→ #9 Emotional Timeline ──→ #14 Chapter Narrative
#19 Emotional Peaks ─┘
                                                      ↑
#11 Milestones ──→ #20 Timeline Slide ───────────────┘

#5 Face Clustering ──→ #13 Photo Curation (migliore se sa chi c'è)

#6 Cover + Stats ←── indipendente (fai quando vuoi)
#7 Monthly Recap ←── indipendente
#8 HTML Export   ←── indipendente (dopo PPTX ok)

#10 Moments ←── usa ranking stage esistente
#12 Smart Quotes ←── usa parse stage esistente
```

---

## Stack tecnica per feature non ancora implementate

| Feature | Librerie / Modelli | VRAM |
|---------|-------------------|------|
| Face Clustering | `insightface` o `facenet-pytorch` + sklearn DBSCAN | ~2GB |
| Emotional Timeline | GPT-OSS (no GPU extra) | — |
| Movie Trailer | `moviepy` + `pydub` | CPU only |
| Memory Graph | `networkx` + `pyvis` per HTML | CPU only |
| HTML Export | `jinja2` + base64 images | CPU only |
| Word Cloud | `wordcloud` library | CPU only |
| Mood Classification | GPT-OSS | — |
| Milestones | GPT-OSS + keyword regex | — |
