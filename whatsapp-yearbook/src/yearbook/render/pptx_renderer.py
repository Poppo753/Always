from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Pt

from yearbook.contracts.reasoning import DailySummary
from yearbook.pipeline.state import PipelineState
from yearbook.render.collage_builder import CollageBuilder

logger = logging.getLogger(__name__)


def _hex(h: str) -> RGBColor:
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _pct(total: int, frac: float) -> Emu:
    return Emu(int(total * frac))


class SlideConfig:
    def __init__(self, cfg: dict[str, Any]) -> None:
        slide_cfg = cfg.get("slide", {})
        self.W = slide_cfg.get("width_emu", 9144000)
        self.H = slide_cfg.get("height_emu", 5143500)

        colors = slide_cfg.get("colors", {})
        self.bg = _hex(colors.get("background", "1C1C2E"))
        self.title_color = _hex(colors.get("title", "FFFFFF"))
        self.body_color = _hex(colors.get("body_text", "E0E0E0"))
        self.accent = _hex(colors.get("accent", "C9A84C"))
        self.quote_color = _hex(colors.get("quote_text", "A8D8EA"))
        self.stats_color = _hex(colors.get("stats_text", "888888"))

        fonts = slide_cfg.get("fonts", {})
        self.title_pt = Pt(fonts.get("title_size", 32))
        self.body_pt = Pt(fonts.get("body_size", 13))
        self.quote_pt = Pt(fonts.get("quote_size", 14))
        self.stats_pt = Pt(fonts.get("stats_size", 10))

        layout = slide_cfg.get("layout", {})
        self.lay = layout

        collage_cfg = cfg.get("collage", {})
        self.max_images = collage_cfg.get("max_images", 4)


class PptxRenderer:
    def __init__(self, state: PipelineState) -> None:
        self.paths = state.paths
        self.scfg = SlideConfig(state.config.get("rendering", state.config))
        self.collage = CollageBuilder()
        self._video_thumbs_by_date: dict[str, list[Path]] = self._build_video_thumb_index()

    def _build_video_thumb_index(self) -> dict[str, list[Path]]:
        """Maps date -> list of video thumbnail paths for days that have videos."""
        import json
        from yearbook.contracts.media import VideoAnalysisRecord
        from yearbook.storage.jsonl_store import JsonlStore

        result: dict[str, list[Path]] = {}
        if not self.paths.media_registry.exists() or not self.paths.video_analysis.exists():
            return result

        reg = json.loads(self.paths.media_registry.read_text('utf-8'))
        date_by_id = {k: v.get('date', '') for k, v in reg.items()}

        thumbs_dir = self.paths.cache_video_frames
        for vid in JsonlStore(self.paths.video_analysis).read_all(VideoAnalysisRecord):
            date = date_by_id.get(vid.media_id, '')
            if not date:
                continue
            thumb = thumbs_dir / f"{vid.media_id}_thumb.jpg"
            if thumb.exists():
                result.setdefault(date, []).append(thumb)
        return result

    def render(self, summaries: list[DailySummary]) -> Presentation:
        prs = Presentation()
        prs.slide_width = Emu(self.scfg.W)
        prs.slide_height = Emu(self.scfg.H)

        blank_layout = prs.slide_layouts[6]  # blank layout

        for summary in summaries:
            slide = prs.slides.add_slide(blank_layout)
            self._set_background(slide)
            self._add_date_label(slide, summary.date)
            self._add_title(slide, summary.title)
            self._add_body(slide, summary)
            self._add_image_area(slide, summary)
            self._add_stats_bar(slide, summary)

        return prs

    # ------------------------------------------------------------------
    # Slide element helpers
    # ------------------------------------------------------------------

    def _set_background(self, slide: Any) -> None:
        from pptx.util import Emu as _E
        from pptx.oxml.ns import qn
        import lxml.etree as etree

        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = self.scfg.bg

    def _add_date_label(self, slide: Any, date_str: str) -> None:
        """Small date in accent color top-right."""
        W, H = self.scfg.W, self.scfg.H
        txb = slide.shapes.add_textbox(
            _pct(W, 0.78), _pct(H, 0.04), _pct(W, 0.18), _pct(H, 0.07)
        )
        tf = txb.text_frame
        tf.text = date_str
        tf.paragraphs[0].alignment = 2  # RIGHT
        run = tf.paragraphs[0].runs[0]
        run.font.size = self.scfg.stats_pt
        run.font.color.rgb = self.scfg.accent

    def _add_title(self, slide: Any, title: str) -> None:
        W, H = self.scfg.W, self.scfg.H
        lay = self.scfg.lay
        txb = slide.shapes.add_textbox(
            _pct(W, lay.get("title_left_pct", 0.04)),
            _pct(H, lay.get("title_top_pct", 0.04)),
            _pct(W, lay.get("title_width_pct", 0.92)),
            _pct(H, lay.get("title_height_pct", 0.12)),
        )
        tf = txb.text_frame
        tf.word_wrap = True
        tf.text = title
        p = tf.paragraphs[0]
        run = p.runs[0]
        run.font.size = self.scfg.title_pt
        run.font.bold = True
        run.font.color.rgb = self.scfg.title_color

    def _add_body(self, slide: Any, summary: DailySummary) -> None:
        W, H = self.scfg.W, self.scfg.H
        lay = self.scfg.lay
        txb = slide.shapes.add_textbox(
            _pct(W, lay.get("body_left_pct", 0.04)),
            _pct(H, lay.get("body_top_pct", 0.18)),
            _pct(W, lay.get("body_width_pct", 0.54)),
            _pct(H, lay.get("body_height_pct", 0.60)),
        )
        tf = txb.text_frame
        tf.word_wrap = True

        from pptx.util import Pt

        # Summary paragraph
        p = tf.paragraphs[0]
        p.space_after = Pt(8)
        run = p.add_run()
        run.text = summary.summary
        run.font.size = self.scfg.body_pt
        run.font.color.rgb = self.scfg.body_color

        # Key moments
        for moment in summary.key_moments:
            p2 = tf.add_paragraph()
            p2.space_before = Pt(4)
            run2 = p2.add_run()
            run2.text = f"• {moment}"
            run2.font.size = self.scfg.body_pt
            run2.font.color.rgb = self.scfg.body_color

        # Quote
        if summary.quote:
            p3 = tf.add_paragraph()
            p3.space_before = Pt(12)
            run3 = p3.add_run()
            run3.text = f'"{summary.quote}"'
            run3.font.size = self.scfg.quote_pt
            run3.font.italic = True
            run3.font.color.rgb = self.scfg.quote_color

    def _add_image_area(self, slide: Any, summary: DailySummary) -> None:
        W, H = self.scfg.W, self.scfg.H
        lay = self.scfg.lay

        left = _pct(W, lay.get("image_left_pct", 0.60))
        top = _pct(H, lay.get("image_top_pct", 0.16))
        width = _pct(W, lay.get("image_width_pct", 0.36))
        height = _pct(H, lay.get("image_height_pct", 0.55))

        image_paths = self._resolve_image_paths(summary.selected_image_media_ids)
        video_thumbs = self._video_thumbs_by_date.get(summary.date, [])
        # Video thumbs first (more visual), then photos, capped at max_images
        combined = (video_thumbs + image_paths)[:self.scfg.max_images]

        if not combined:
            return

        collage_img = self.collage.build(combined)
        if collage_img is None:
            return

        buf = io.BytesIO()
        collage_img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        slide.shapes.add_picture(buf, left, top, width, height)

    def _add_stats_bar(self, slide: Any, summary: DailySummary) -> None:
        W, H = self.scfg.W, self.scfg.H
        lay = self.scfg.lay

        mood_label = f"mood: {summary.mood}"
        stats = summary.stats or {}
        parts = [mood_label]
        if stats.get("message_count"):
            parts.append(f"{stats['message_count']} msgs")
        if stats.get("image_count"):
            parts.append(f"{stats['image_count']} photos")

        txb = slide.shapes.add_textbox(
            _pct(W, lay.get("stats_left_pct", 0.04)),
            _pct(H, lay.get("stats_top_pct", 0.88)),
            _pct(W, lay.get("stats_width_pct", 0.92)),
            _pct(H, lay.get("stats_height_pct", 0.10)),
        )
        tf = txb.text_frame
        tf.text = "  ·  ".join(parts)
        p = tf.paragraphs[0]
        if p.runs:
            run = p.runs[0]
            run.font.size = self.scfg.stats_pt
            run.font.color.rgb = self.scfg.stats_color

    def _resolve_image_paths(self, media_ids: list[str]) -> list[Path]:
        """Look up actual file paths from media registry."""
        try:
            import json
            registry_path = self.paths.media_registry
            if not registry_path.exists():
                return []
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            # Registry is stored as dict {media_id: record} or list of records
            if isinstance(data, dict):
                lookup = {k: v for k, v in data.items() if "media_id" in v}
            else:
                lookup = {item["media_id"]: item for item in data if "media_id" in item}
            paths = []
            for mid in media_ids:
                rec = lookup.get(mid)
                if rec:
                    # relative_path is the actual field in the registry (not file_path)
                    rel = rec.get("relative_path") or rec.get("file_path")
                    if rel:
                        p = self.paths.root / rel
                        if p.exists():
                            paths.append(p)
            return paths
        except Exception as exc:
            logger.warning("Could not resolve image paths: %s", exc)
            return []


def run_render(state: PipelineState) -> None:
    """Render daily summaries into a PPTX yearbook."""
    paths = state.paths

    summary_files = sorted(paths.daily_summaries_dir.glob("*.json"))
    logger.info("Found %d summary files to render", len(summary_files))

    if not summary_files:
        logger.warning("No summary files found. Cannot render PPTX.")
        return

    summaries = []
    for sf in summary_files:
        try:
            summaries.append(DailySummary.model_validate_json(sf.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.error("Failed to load summary %s: %s", sf, exc)

    renderer = PptxRenderer(state)
    prs = renderer.render(summaries)

    paths.output_dir.mkdir(parents=True, exist_ok=True)
    prs.save(str(paths.pptx_output))
    logger.info("PPTX yearbook saved to: %s", paths.pptx_output)
