"""Trace image flow for a specific day."""
import json, sys
from pathlib import Path

day = sys.argv[1] if len(sys.argv) > 1 else "2025-03-11"

bp = Path(f"runs/run_001/day_bundles/{day}.json")
if bp.exists():
    b = json.loads(bp.read_text("utf-8"))
    print(f"=== DAY BUNDLE {day} ===")
    print(f"  image_analysis_ids: {b.get('image_analysis_ids', [])}")
    print(f"  video_analysis_ids: {b.get('video_analysis_ids', [])}")
    print(f"  message_count: {b.get('message_count', '?')}")

cp = Path(f"runs/run_001/daily_contexts/{day}.json")
if cp.exists():
    c = json.loads(cp.read_text("utf-8"))
    print(f"=== CONTEXT {day} ===")
    imgs = c.get("top_images", [])
    print(f"  top_images: {len(imgs)}")
    for img in imgs[:5]:
        print(f"    {img['media_id']}: {img.get('caption','?')[:60]}")
    print(f"  stats: {c.get('stats', {})}")

rp = Path(f"runs/run_001/daily_reasoning/{day}.json")
if rp.exists():
    r = json.loads(rp.read_text("utf-8"))
    print(f"=== REASONING {day} ===")
    print(f"  selected_image_media_ids: {r.get('selected_image_media_ids', [])}")
    print(f"  selected_quote: {r.get('selected_quote_message_id')}")

sp = Path(f"runs/run_001/daily_summaries/{day}.json")
if sp.exists():
    s = json.loads(sp.read_text("utf-8"))
    print(f"=== SUMMARY {day} ===")
    print(f"  selected_image_media_ids: {s.get('selected_image_media_ids', [])}")
