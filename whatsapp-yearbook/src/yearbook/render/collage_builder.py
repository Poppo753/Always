from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# Max images composited in one collage
MAX_IMAGES = 4


class CollageBuilder:
    """Builds a single PIL composite image from up to 4 source images."""

    def __init__(
        self,
        target_width: int = 720,
        target_height: int = 540,
    ) -> None:
        self.target_width = target_width
        self.target_height = target_height

    def build(self, image_paths: list[Path]) -> Optional[Image.Image]:
        """
        Compose up to MAX_IMAGES images into a grid collage.
        Returns None if no valid images are provided.
        """
        valid: list[Image.Image] = []
        for p in image_paths[:MAX_IMAGES]:
            try:
                img = Image.open(p).convert("RGB")
                valid.append(img)
            except Exception as exc:
                logger.warning("Could not open image %s: %s", p, exc)

        if not valid:
            return None

        if len(valid) == 1:
            return self._resize(valid[0], self.target_width, self.target_height)

        return self._grid(valid)

    def _resize(self, img: Image.Image, w: int, h: int) -> Image.Image:
        return img.resize((w, h), Image.LANCZOS)

    def _grid(self, images: list[Image.Image]) -> Image.Image:
        """Lay out 2-4 images in a grid (2-col) with equal-sized cells."""
        cols = 2
        rows = (len(images) + 1) // 2
        cell_w = self.target_width // cols
        cell_h = self.target_height // rows
        canvas = Image.new("RGB", (self.target_width, self.target_height), (28, 28, 46))
        for idx, img in enumerate(images):
            col = idx % cols
            row = idx // cols
            thumb = self._resize(img, cell_w, cell_h)
            x = col * cell_w
            y = row * cell_h
            canvas.paste(thumb, (x, y))
        return canvas
