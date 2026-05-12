from __future__ import annotations

from datetime import datetime
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = PACKAGE_DIR.parent
SKILL_ROOT = SCRIPTS_DIR.parent


def timestamped_output_dir(base: Path | None = None) -> Path:
    root = base or Path.cwd()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = root / f"resume_output_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def first_existing(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def resolve_data_file(filename: str, explicit: str | None = None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.exists() else None
    return first_existing([
        Path.cwd() / "data" / filename,
        SKILL_ROOT / "data" / filename,
    ])


def resolve_experiences(explicit: str | None = None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.exists() else None
    return first_existing([
        Path.cwd() / "data" / "my_experiences.local.json",
        Path.cwd() / "data" / "my_experiences.json",
        SKILL_ROOT / "data" / "my_experiences.local.json",
        SKILL_ROOT / "data" / "my_experiences.json",
        SKILL_ROOT / "data" / "my_experiences.example.json",
    ])


def resolve_profile(explicit: str | None = None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.exists() else None
    return first_existing([
        Path.cwd() / "data" / "my_profile.local.json",
        Path.cwd() / "data" / "my_profile.json",
        SKILL_ROOT / "data" / "my_profile.local.json",
        SKILL_ROOT / "data" / "my_profile.json",
    ])


def resolve_template(name_or_path: str) -> Path:
    raw = Path(name_or_path).expanduser()
    candidates = [
        raw,
        Path.cwd() / "templates" / name_or_path,
        SKILL_ROOT / "templates" / name_or_path,
    ]
    for path in candidates:
        if (path / "template.html").exists() and (path / "style.css").exists():
            return path
    raise FileNotFoundError(
        f"Template not found: {name_or_path}. Expected template.html and style.css."
    )
