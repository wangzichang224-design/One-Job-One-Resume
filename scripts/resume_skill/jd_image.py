"""Optional JD screenshot OCR using a configured vision API."""

from __future__ import annotations

import base64
import os
from pathlib import Path


def load_env() -> tuple[str | None, str]:
    candidates = [Path.cwd() / ".env", Path.home() / ".env"]
    values: dict[str, str] = {}
    for env_path in candidates:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
    key = os.environ.get("VISION_API_KEY") or values.get("VISION_API_KEY")
    provider = os.environ.get("VISION_API_PROVIDER") or values.get("VISION_API_PROVIDER") or "openai"
    return key, provider.lower().strip()


def parse_jd_image(image_path: str) -> str:
    api_key, provider = load_env()
    if not api_key:
        raise RuntimeError(
            "No VISION_API_KEY found. Paste the JD text manually, or let the Agent read the screenshot and save jd.txt."
        )
    if provider == "anthropic":
        return parse_with_anthropic(Path(image_path), api_key)
    if provider == "openai":
        return parse_with_openai(Path(image_path), api_key)
    raise ValueError(f"Unsupported VISION_API_PROVIDER: {provider}")


def media_type(path: Path) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/png")


def image_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def parse_with_openai(path: Path, api_key: str) -> str:
    import httpx

    data_uri = f"data:{media_type(path)};base64,{image_b64(path)}"
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this job description screenshot. Output only the text."},
                    {"type": "image_url", "image_url": {"url": data_uri, "detail": "high"}},
                ],
            }],
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return "\n".join(choice["message"]["content"] for choice in data.get("choices", [])).strip()


def parse_with_anthropic(path: Path, api_key: str) -> str:
    import httpx

    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this job description screenshot. Output only the text."},
                    {"type": "image", "source": {"type": "base64", "media_type": media_type(path), "data": image_b64(path)}},
                ],
            }],
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return "\n".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text").strip()
