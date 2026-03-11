from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(project_root: Path) -> dict[str, Any]:
    """Load and merge default.yaml with any local overrides."""
    config_dir = project_root / "config"
    cfg = load_yaml(config_dir / "default.yaml")

    # Load supplementary configs
    for extra in ["ranking.yaml", "prompts.yaml", "rendering.yaml"]:
        extra_path = config_dir / extra
        if extra_path.exists():
            cfg[extra.replace(".yaml", "")] = load_yaml(extra_path)

    return cfg
