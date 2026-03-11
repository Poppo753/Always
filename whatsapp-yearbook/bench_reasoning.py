"""Benchmark gpt-oss:20b vs qwen3:8b on 10 days."""
import time, json, statistics
from pathlib import Path
from yearbook.ai.gpt_oss_client import GptOssClient
from yearbook.contexts.context_builder import DailyContextBuilder
from yearbook.contracts.reasoning import DailyContext

PROMPT = (
    "You are analyzing a day in a romantic conversation between two people.\n"
    "Based on the structured context below, identify the main theme, mood, and significance of the day.\n\n"
    "Return a JSON object with these exact fields:\n"
    '{"main_theme": "brief description",\n'
    ' "day_type": "one of: quiet_day, social_evening, outing, emotional_moment, planning_day, milestone, mixed",\n'
    ' "importance_level": "one of: low, medium, high",\n'
    ' "mood": "one of: warm_playful, romantic, nostalgic, cheerful, neutral, tense, melancholy, excited",\n'
    ' "reasoning_summary": "2-3 sentences explaining what this day was about",\n'
    ' "evidence": {"message_ids": [], "event_ids": [], "media_ids": []},\n'
    ' "selected_quote_message_id": null,\n'
    ' "selected_image_media_ids": []}\n'
    "Return ONLY the JSON, no other text.\n\nCONTEXT:\n"
)

ctxs = sorted(Path("runs/run_001/daily_contexts").glob("*.json"))[:10]
builder = DailyContextBuilder()

contexts = []
for cp in ctxs:
    ctx = DailyContext.model_validate_json(cp.read_text("utf-8"))
    txt = builder.to_text(ctx)
    contexts.append((ctx.date, txt))

print(f"Testing {len(contexts)} days\n")

for model_name in ["gpt-oss:20b", "qwen3:8b"]:
    client = GptOssClient(model_name=model_name, timeout=180)

    print(f"=== {model_name} ===")
    print("  Warmup (loading model)...")
    t0 = time.time()
    client.reason_day(contexts[0][1], PROMPT)
    warmup = time.time() - t0
    print(f"  Warmup: {warmup:.1f}s")

    times = []
    results = []
    for date, txt in contexts:
        t0 = time.time()
        raw = client.reason_day(txt, PROMPT)
        elapsed = time.time() - t0
        times.append(elapsed)
        results.append((date, raw))
        theme = raw.get("main_theme", "?")[:60] if raw else "FAILED"
        print(f"  {date}: {elapsed:.1f}s | {theme}")

    avg = statistics.mean(times)
    med = statistics.median(times)
    total_353 = avg * 353
    print(f"  ---")
    print(f"  Avg: {avg:.1f}s | Median: {med:.1f}s | Est 353 days: {total_353/60:.0f} min ({total_353/3600:.1f}h)")

    # Sample output for quality comparison
    sample = results[2] if len(results) > 2 else results[0]
    print(f"\n  Sample output ({sample[0]}):")
    print(f"  {json.dumps(sample[1], indent=2)[:800]}")
    print()
