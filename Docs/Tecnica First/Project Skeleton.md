# 1. Project Skeleton reale

## 1.1 Obiettivo

Definire la struttura reale del repository e delle componenti software per portare il progetto dal design all’implementazione.

## 1.2 Struttura repository consigliata

```text
whatsapp-yearbook/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── config/
│   ├── default.yaml
│   ├── prompts.yaml
│   ├── ranking.yaml
│   ├── rendering.yaml
│   └── models.yaml
├── input/
│   ├── _chat.txt
│   └── media/
├── runs/
│   └── .gitkeep
├── cache/
│   ├── images/
│   ├── audio/
│   ├── reasoning/
│   ├── summaries/
│   └── embeddings/
├── logs/
│   └── .gitkeep
├── templates/
│   ├── base_yearbook.pptx
│   └── slide_theme_minimal.json
├── schemas/
│   ├── message_record.schema.json
│   ├── media_registry_record.schema.json
│   ├── image_analysis_record.schema.json
│   ├── voice_transcript_record.schema.json
│   ├── event_record.schema.json
│   ├── ranked_day_assets.schema.json
│   ├── daily_context.schema.json
│   ├── daily_reasoning.schema.json
│   ├── daily_summary.schema.json
│   ├── run_manifest.schema.json
│   └── run_report.schema.json
├── src/
│   └── yearbook/
│       ├── __init__.py
│       ├── main.py
│       ├── cli.py
│       ├── constants.py
│       ├── exceptions.py
│       ├── paths.py
│       ├── logging_config.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── models.py
│       ├── contracts/
│       │   ├── __init__.py
│       │   ├── messages.py
│       │   ├── media.py
│       │   ├── events.py
│       │   ├── ranking.py
│       │   ├── reasoning.py
│       │   ├── summaries.py
│       │   └── run.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── jsonl_store.py
│       │   ├── parquet_store.py
│       │   ├── cache_store.py
│       │   └── manifest_store.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── hashing.py
│       │   ├── datetime_utils.py
│       │   ├── text_utils.py
│       │   ├── file_utils.py
│       │   ├── image_utils.py
│       │   └── retry.py
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── orchestrator.py
│       │   ├── stages.py
│       │   ├── state.py
│       │   └── job_queue.py
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── input_validator.py
│       │   ├── inventory_builder.py
│       │   └── bootstrap.py
│       ├── parsing/
│       │   ├── __init__.py
│       │   ├── whatsapp_parser.py
│       │   ├── attachment_matcher.py
│       │   └── message_normalizer.py
│       ├── media/
│       │   ├── __init__.py
│       │   ├── registry_builder.py
│       │   ├── image_analyzer.py
│       │   ├── voice_transcriber.py
│       │   ├── image_scorer.py
│       │   └── media_selectors.py
│       ├── events/
│       │   ├── __init__.py
│       │   ├── temporal_clusterer.py
│       │   ├── event_detector.py
│       │   ├── event_classifier.py
│       │   └── event_scorer.py
│       ├── ranking/
│       │   ├── __init__.py
│       │   ├── message_ranker.py
│       │   ├── voice_ranker.py
│       │   ├── day_asset_ranker.py
│       │   └── anti_noise.py
│       ├── contexts/
│       │   ├── __init__.py
│       │   ├── day_grouper.py
│       │   ├── stats_builder.py
│       │   ├── context_builder.py
│       │   └── quote_selector.py
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── qwen_vl_client.py       │   ├── gpt_oss_client.py│       │   ├── whisper_client.py
│       │   ├── prompt_builder.py
│       │   ├── json_repair.py
│       │   └── output_validator.py
│       ├── reasoning/
│       │   ├── __init__.py
│       │   ├── day_reasoner.py
│       │   ├── mood_classifier.py
│       │   └── signal_interpreter.py
│       ├── summaries/
│       │   ├── __init__.py
│       │   ├── narrative_generator.py
│       │   ├── summary_postprocessor.py
│       │   └── factual_guard.py
│       ├── render/
│       │   ├── __init__.py
│       │   ├── pptx_renderer.py
│       │   ├── collage_builder.py
│       │   ├── slide_layout.py
│       │   ├── preview_exporter.py
│       │   └── text_fit.py
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── json_schema_validator.py
│       │   ├── contract_checks.py
│       │   └── input_sanity.py
│       └── reports/
│           ├── __init__.py
│           ├── run_report_builder.py
│           └── diagnostics.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── small_chat/
    │   ├── noisy_chat/
    │   └── media_samples/
    ├── test_parser.py
    ├── test_media_registry.py
    ├── test_image_analysis.py
    ├── test_voice_transcription.py
    ├── test_event_detection.py
    ├── test_ranking.py
    ├── test_context_builder.py
    ├── test_reasoning.py
    ├── test_summary_generation.py
    ├── test_renderer.py
    └── test_end_to_end_small_run.py
```

## 1.3 File entrypoints principali

### `src/yearbook/main.py`

Responsabilità:

* entrypoint applicativo
* bootstrap run
* invocazione orchestratore

### `src/yearbook/cli.py`

Responsabilità:

* interfaccia CLI
* comandi come:

  * `bootstrap`
  * `parse`
  * `analyze-media`
  * `detect-events`
  * `build-contexts`
  * `reason`
  * `summarize`
  * `render`
  * `run-all`

## 1.4 Classi core consigliate

### `RunContext`

Campi:

* run_id
* project_root
* input_dir
* output_dir
* config
* logger

### `PipelineOrchestrator`

Metodi:

* `run_all()`
* `run_stage(stage_name)`
* `resume_from(stage_name)`

### `WhatsAppParser`

Metodi:

* `parse_chat_file(path)`
* `normalize_messages(raw_messages)`

### `MediaRegistryBuilder`

Metodi:

* `build_registry(messages, media_dir)`
* `compute_media_hashes()`

### `QwenVLClient`

Metodi:

* `analyze_image(image_path, prompt)` — multimodal perception only (caption, OCR, classification)

Nota: QwenVLClient **non** esegue reasoning finale. Il metodo `reason_day` è stato rimosso. Il reasoning è delegato a `GptOssClient`.

### `GptOssClient`

Metodi:

* `reason_day(daily_context, prompt)` — reasoning e interpretazione del giorno
* `generate_summary(reasoning_output, prompt)` — generazione narrativa

### `WhisperClient`

Metodi:

* `transcribe(audio_path)`

### `EventDetector`

Metodi:

* `detect_events(day_messages, media_records)`

### `DayAssetRanker`

Metodi:

* `rank_day_assets(day_bundle)`

### `DailyContextBuilder`

Metodi:

* `build(day_bundle, events, ranked_assets, analyses)`

### `DayReasoner`

Metodi:

* `reason(day_context)` — invoca GPT-OSS-20B tramite `GptOssClient`

### `NarrativeGenerator`

Metodi:

* `generate(reasoning_output)` — invoca GPT-OSS-20B tramite `GptOssClient`

### `PptxRenderer`

Metodi:

* `render_day_slide(summary, assets)`
* `render_deck(all_day_summaries)`

## 1.5 Pipeline stub raccomandata

```python
class PipelineOrchestrator:
    def run_all(self) -> None:
        self.bootstrap()
        self.parse_chat()
        self.build_media_registry()
        self.analyze_media()
        self.group_days()
        self.detect_events()
        self.rank_assets()
        self.build_contexts()
        self.reason_days()
        self.summarize_days()
        self.render_presentation()
        self.write_run_report()
```

## 1.6 Dipendenze raccomandate

### Core

* python 3.11+
* pydantic
* pandas
* pyarrow
* pillow
* python-pptx
* jsonschema
* rich
* typer oppure click
* pyyaml

### AI

* torch
* transformers
* accelerate
* sentencepiece
* whisper / faster-whisper

### Storage / search opzionali

* duckdb
* faiss-cpu oppure faiss-gpu

## 1.7 Modalità di sviluppo consigliata

* modulo per modulo
* sempre con fixture piccole
* prima pipeline sincrona e semplice
* solo dopo aggiungere queue/resume