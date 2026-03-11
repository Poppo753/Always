import json
from pathlib import Path
from yearbook.ai.gpt_oss_client import GptOssClient

PROMPT = (
    "You are analyzing a day in a romantic conversation between two people.\n"
    "Based on the context below, return ONLY a JSON object with these exact fields:\n"
    '{"main_theme": "", "day_type": "quiet_day", "importance_level": "medium", '
    '"mood": "neutral", "reasoning_summary": "", '
    '"evidence": {"message_ids": [], "event_ids": [], "media_ids": []}, '
    '"selected_quote_message_id": null, "selected_image_media_ids": []}\n'
    "Return ONLY the JSON, no other text.\n\nCONTEXT:\n"
)

ctx = json.loads(Path("runs/run_001/daily_contexts/2025-03-10.json").read_text(encoding="utf-8"))
ctx_text = json.dumps(ctx, ensure_ascii=False)[:1200]

client = GptOssClient(model_name="gpt-oss:20b", base_url="http://localhost:11434", timeout=90)
result = client.reason_day(ctx_text, PROMPT)
print("GPT-OSS OK:", result is not None)
if result:
    print(json.dumps(result, ensure_ascii=False, indent=2)[:600])
else:
    print("FAIL: returned None")
