from __future__ import annotations

import shutil
from pathlib import Path

from .paths import SKILL_ROOT


def copy_if_missing(source: Path, target: Path) -> bool:
    if target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def init_workspace(base: Path | None = None) -> list[str]:
    root = base or Path.cwd()
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    messages: list[str] = []

    files = [
        ("my_profile.example.json", "my_profile.local.json"),
        ("my_experiences.example.json", "my_experiences.local.json"),
    ]
    for source_name, target_name in files:
        created = copy_if_missing(SKILL_ROOT / "data" / source_name, data_dir / target_name)
        status = "created" if created else "kept"
        messages.append(f"{status}: {data_dir / target_name}")

    templates_dir = root / "templates"
    templates_dir.mkdir(exist_ok=True)
    messages.append(f"template folder ready: {templates_dir}")
    messages.append("put your photo at data/photo.png, then edit the two .local.json files")
    return messages
