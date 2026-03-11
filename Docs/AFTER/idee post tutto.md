Ci penso seriamente. Guardo cosa abbiamo e cosa manca: 

Ran terminal command: cd D:\Documents\Projects\Ana\whatsapp-yearbook; python -c "
import json
from pathlib import Path
reg = json.loads(Path('runs/run_001/media_registry.json').read_text('utf-8'))

# Docs
docs = [v for v in reg.values() if v.get('media_kind') == 'document']
print('Documents:', len(docs), [v['filename'] for v in docs[:5]])

# Deduplication
dupes = [v for v in reg.values() if v.get('dedupe_group_id')]
print('Deduplicati:', len(dupes))

# Stickers
stickers = [v for v in reg.values() if v.get('media_kind') == 'sticker']
print('Stickers totali:', len(stickers))

# Senders
senders = {}
for v in reg.values():
    s = v.get('sender','?')
    senders[s] = senders.get(s,0)+1
print('Mittenti:', senders)
"

Ran terminal command: cd D:\Documents\Projects\Ana\whatsapp-yearbook; python -c "
import json
from pathlib import Path

# Check ranking contract and rendering to understand gaps
print('=== RENDER ===')
from yearbook.render.pptx_renderer import run_render
import inspect
print(inspect.getsource(run_render)[:3000])
" 2>&1 | Select-Object -First 80

Ho tutto quello che mi serve. Ecco un'analisi completa, prioritizzata per impatto reale:

---

## Cosa aggiungere — priorità alta → bassa

### 🔴 ALTO impatto, poco lavoro

**1. Lingua output italiana**
Tutti i prompt sono in inglese → Qwen e GPT-OSS rispondono in inglese → yearbook in inglese. Ma la chat è in spagnolo/italiano. Basta aggiungere `"Respond in Italian."` ai prompt di reasoning/summarize.

**2. Cover page + stats page**
Il PPTX attuale inizia direttamente con le giornate. Manca:
- **Copertina**: migliore foto dell'anno + titolo + "Ana & Lorenzo • 2025-2026"
- **Pagina stats**: totale messaggi, foto, audio, giorni insieme, primo/ultimo messaggio, "giorno più intenso"

**3. Documenti (8 file, completamente ignorati)**
Il boarding pass `Milan-Montreal`, il CV di Ana, il comprobante de estudios — sono pezzi di storia! Bastano 2 cose: OCR + classificazione → `document_analysis` stage.

**4. Video thumbnail nel PPTX**
I video sono analizzati ma nel PPTX non compare nulla. Estrarre il frame migliore (quello con `aesthetic_score` più alto) e includerlo come immagine nella slide.

---

### 🟡 MEDIO impatto, lavoro medio

**5. Face clustering (riconoscimento ricorrente senza nomi)**
Senza API esterne, con `insightface` o `deepface` si possono raggruppare facce ricorrenti → "persona A appare in 47 foto", "persona A + persona B insieme in 23 foto" → rilevanza narrativa molto più precisa. Potente per capire chi sono i protagonisti.

**6. Sentiment / tono della conversazione**
Analizzare l'emozione di ogni giornata non solo dal contenuto ma dal tono: quante emoji di cuore? quante di risata? quante di preoccupazione? → `mood_score` per giorno → grafico evoluzione nel tempo.

**7. Event clustering multi-giorno**
Attualmente ogni giorno è isolato. Un viaggio o un weekend si spalma su 3-4 giorni — dovrebbe essere un **unico evento** con narrative comune. Serve clustering temporale con gap tolerance.

**8. "Momenti migliori" per mese**
Una slide di recap mensile: foto migliore del mese, frase più bella, stat del mese → struttura yearbook molto più leggibile.

---

### 🟢 BASSO impatto / nicchia

**9. Export HTML/web**
Oltre al PPTX, un file HTML statico (immagini embedded in base64) sarebbe più condivisibile e visibile su qualsiasi dispositivo — specialmente su mobile.

**10. Location parsing**
WhatsApp condivide coordinate GPS come messaggi speciali — il parser probabilmente le ignora. Potrebbero diventare "sent from Milan", "sent from Montreal" nella narrative.

**11. Word cloud per mese**
Parole più usate per mese → tile visiva nel PPTX.

**12. Quote inteligente automatica**
Invece di scegliere quote lunghe, cercare messaggi con pattern emotivi forti (`"ti amo"`, `"non ci credo"`, `"finalmente"`) + brevi + non banali.

---

## Priorità suggerita

```
Ora (prima del PPTX finale):
  1. Lingua italiana nei prompt
  2. Video thumbnail nel PPTX

Prossima iterazione:
  3. Cover + stats page
  4. Documenti OCR
  5. Event clustering multi-giorno

Dopo (se vuoi):
  6. Face clustering
  7. Export HTML
```

Vuoi che implementi uno di questi adesso, mentre il pipeline gira?