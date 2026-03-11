import json, subprocess
from pathlib import Path

reg = json.loads(Path('runs/run_001/media_registry.json').read_text('utf-8'))
videos = sorted([v for v in reg.values() if v.get('media_kind') == 'video'], key=lambda x: x.get('size_bytes', 0))

print(f"{'File':<42} {'MB':>6}  {'Sec':>7}  Frames@strat")
print('-' * 72)
total_frames = 0
for v in videos:
    p = Path(v['relative_path'])
    mb = v.get('size_bytes', 0) / 1024 / 1024
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', str(p)],
            capture_output=True, text=True
        )
        info = json.loads(r.stdout)
        dur = float(next((s['duration'] for s in info.get('streams', []) if 'duration' in s), 0))
        # Strategy: 1fps if <30s, 1/5fps if <120s, 1/10fps if <300s, 1/30fps otherwise
        if dur <= 30:
            interval = 1
        elif dur <= 120:
            interval = 5
        elif dur <= 300:
            interval = 10
        else:
            interval = 30
        frames = max(1, int(dur / interval))
        total_frames += frames
        print(f"{v['filename']:<42} {mb:6.2f}  {dur:7.1f}s  {frames} frames (ogni {interval}s)")
    except Exception as e:
        print(f"{v['filename']:<42} {mb:6.2f}  ERR: {e}")

print()
print(f"Totale frames da analizzare: {total_frames} (vs 590 immagini)")
print(f"Stima tempo a 13s/frame: {total_frames*13/60:.0f} min")
