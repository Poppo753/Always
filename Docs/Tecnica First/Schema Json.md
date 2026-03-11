# 2. Schema JSON definitivo

## 2.1 Regole generali

* tutti i record hanno `schema_version`
* timestamp in ISO 8601
* date in formato `YYYY-MM-DD`
* score sempre `0.0 - 1.0` dove possibile
* path sempre relativi alla root del progetto run
* nomi campi stabili e in snake_case

---

## 2.2 `run_manifest.json`

```json
{
  "schema_version": "1.0",
  "run_id": "run_2026_03_10_001",
  "project_name": "whatsapp_yearbook",
  "created_at": "2026-03-10T10:00:00",
  "input_chat_path": "input/_chat.txt",
  "input_media_dir": "input/media",
  "config_snapshot": {
    "model_image": "qwen2.5-vl-7b",
    "model_audio": "whisper-large-v3",
    "model_reasoning": "gpt-oss-20b",
    "year_target": 2025
  }
}
```

---

## 2.3 `message_record`

```json
{
  "schema_version": "1.0",
  "message_id": "msg_000001",
  "source_line_start": 1,
  "source_line_end": 2,
  "timestamp": "2025-01-01T09:34:00",
  "date": "2025-01-01",
  "sender": "Lorenzo",
  "message_type": "text",
  "text": "Buongiornooo",
  "attachment": null,
  "attachment_kind": null,
  "is_system": false,
  "reply_to_message_id": null,
  "language": "it",
  "parse_warnings": []
}
```

Campi ammessi per `message_type`:

* `text`
* `image`
* `video`
* `voice`
* `document`
* `sticker`
* `system`
* `unknown`

---

## 2.4 `media_registry_record`

```json
{
  "schema_version": "1.0",
  "media_id": "media_000123",
  "filename": "IMG-20250101-WA0001.jpg",
  "relative_path": "input/media/IMG-20250101-WA0001.jpg",
  "media_kind": "image",
  "mime_type": "image/jpeg",
  "extension": ".jpg",
  "sha256": "abc123...",
  "size_bytes": 345678,
  "message_id": "msg_000045",
  "timestamp": "2025-01-01T20:11:00",
  "sender": "Marta",
  "date": "2025-01-01",
  "dedupe_group_id": null,
  "exists_on_disk": true
}
```

---

## 2.5 `image_analysis_record`

```json
{
  "schema_version": "1.0",
  "analysis_id": "img_analysis_0001",
  "media_id": "media_000123",
  "filename": "IMG-20250101-WA0001.jpg",
  "model_name": "qwen2.5-vl-7b",
  "prompt_version": "image_caption_v1",
  "caption": "cena sushi in ristorante con due piatti sul tavolo",
  "short_caption": "cena sushi",
  "category": "food_restaurant",
  "subcategory": "dinner",
  "ocr_text": "",
  "people_count_estimate": 0,
  "contains_screenshot": false,
  "contains_document_like_layout": false,
  "contains_meme": false,
  "tags": ["restaurant", "food", "dinner"],
  "aesthetic_score": 0.71,
  "narrative_relevance_score": 0.84,
  "technical_quality_score": 0.78,
  "confidence": 0.87,
  "warnings": []
}
```

---

## 2.6 `voice_transcript_record`

```json
{
  "schema_version": "1.0",
  "transcript_id": "voice_tx_0001",
  "media_id": "media_000200",
  "filename": "PTT-20250101-WA0003.opus",
  "model_name": "whisper-large-v3",
  "duration_seconds": 42.3,
  "language": "it",
  "transcript": "Ci sentiamo dopo cena, non vedo l'ora di raccontarti tutto.",
  "short_summary": "Vocale affettuoso sul vedersi dopo cena",
  "confidence": 0.82,
  "warnings": []
}
```

---

## 2.7 `event_record`

```json
{
  "schema_version": "1.0",
  "event_id": "evt_0001",
  "date": "2025-01-01",
  "time_start": "2025-01-01T19:40:00",
  "time_end": "2025-01-01T20:20:00",
  "event_type": "outing_meal",
  "confidence": 0.76,
  "description": "Organizzazione e condivisione di una cena sushi",
  "message_ids": ["msg_000032", "msg_000033", "msg_000045"],
  "media_ids": ["media_000123"],
  "trigger_signals": ["planning_phrase", "image_shared", "time_cluster"],
  "score": 0.81
}
```

---

## 2.8 `ranked_day_assets`

```json
{
  "schema_version": "1.0",
  "date": "2025-01-01",
  "top_message_ids": ["msg_000032", "msg_000041", "msg_000052"],
  "top_event_ids": ["evt_0001", "evt_0002"],
  "top_image_media_ids": ["media_000123", "media_000124"],
  "top_voice_media_ids": ["media_000200"],
  "discarded_message_ids": ["msg_000090"],
  "selection_metadata": {
    "message_limit": 12,
    "image_limit": 4,
    "voice_limit": 2,
    "event_limit": 6
  }
}
```

---

## 2.9 `daily_context`

```json
{
  "schema_version": "1.0",
  "date": "2025-01-01",
  "stats": {
    "message_count": 84,
    "image_count": 3,
    "voice_count": 1,
    "video_count": 0,
    "conversation_clusters": 4
  },
  "top_messages": [
    {
      "message_id": "msg_000032",
      "sender": "Lorenzo",
      "timestamp": "2025-01-01T18:31:00",
      "text": "Stasera sushi?",
      "score": 0.74
    }
  ],
  "top_events": [
    {
      "event_id": "evt_0001",
      "event_type": "outing_meal",
      "description": "Organizzazione e condivisione di una cena sushi",
      "score": 0.81
    }
  ],
  "top_images": [
    {
      "media_id": "media_000123",
      "filename": "IMG-20250101-WA0001.jpg",
      "caption": "cena sushi in ristorante",
      "score": 0.84
    }
  ],
  "top_voice_transcripts": [
    {
      "media_id": "media_000200",
      "short_summary": "Vocale affettuoso sul vedersi dopo cena",
      "score": 0.79
    }
  ],
  "candidate_quotes": [
    {
      "message_id": "msg_000041",
      "text": "Non vedo l'ora di vederti",
      "score": 0.83
    }
  ]
}
```

---

## 2.10 `daily_reasoning`

```json
{
  "schema_version": "1.0",
  "date": "2025-01-01",
  "model_name": "gpt-oss-20b",
  "prompt_version": "day_reasoning_v1",
  "main_theme": "Serata insieme e tono affettuoso",
  "day_type": "social_evening",
  "importance_level": "medium",
  "mood": "warm_playful",
  "reasoning_summary": "La giornata ruota attorno all'organizzazione della serata e alla foto della cena, con scambi affettuosi che danno un tono positivo alla chiusura del giorno.",
  "evidence": {
    "message_ids": ["msg_000032", "msg_000041"],
    "event_ids": ["evt_0001"],
    "media_ids": ["media_000123", "media_000200"]
  },
  "selected_quote_message_id": "msg_000041",
  "selected_image_media_ids": ["media_000123"]
}
```

---

## 2.11 `daily_summary`

```json
{
  "schema_version": "1.0",
  "date": "2025-01-01",
  "title": "Sushi, attesa e voglia di vedersi",
  "summary": "Dopo una giornata piuttosto tranquilla, la conversazione si è accesa intorno all'idea di vedersi per una cena sushi. La foto condivisa dal ristorante e i messaggi finali hanno dato alla giornata un tono caldo e affettuoso.",
  "key_moments": [
    "Organizzazione della cena",
    "Foto condivisa dal ristorante",
    "Scambio affettuoso a fine serata"
  ],
  "quote": "Non vedo l'ora di vederti",
  "mood": "warm_playful",
  "selected_image_media_ids": ["media_000123"],
  "stats": {
    "message_count": 84,
    "image_count": 3,
    "voice_count": 1
  },
  "source_evidence": {
    "message_ids": ["msg_000032", "msg_000041"],
    "event_ids": ["evt_0001"],
    "media_ids": ["media_000123", "media_000200"]
  }
}
```

---

## 2.12 `run_report.json`

```json
{
  "schema_version": "1.0",
  "run_id": "run_2026_03_10_001",
  "started_at": "2026-03-10T10:00:00",
  "finished_at": "2026-03-10T10:41:00",
  "total_days_processed": 365,
  "total_messages": 28412,
  "total_images": 1210,
  "total_voices": 143,
  "cache_hit_ratio": 0.64,
  "failed_assets": 3,
  "warnings": [
    "2 immagini corrotte saltate",
    "1 vocale con trascrizione incompleta"
  ],
  "output_pptx": "runs/run_2026_03_10_001/output/yearbook_2025.pptx"
}
```

---
