from __future__ import annotations

import shutil
import subprocess
import re
from pathlib import Path


def find_browser() -> str | None:
    for command in ["msedge", "chrome", "google-chrome", "chromium"]:
        found = shutil.which(command)
        if found:
            return found
    for path in [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]:
        if path.exists():
            return str(path)
    return None


def html_to_pdf(html_path: Path, pdf_path: Path) -> tuple[bool, str]:
    browser = find_browser()
    if not browser:
        return False, "Chrome/Edge not found; resume.html is still ready to open or print."
    browser_profile = pdf_path.parent / ".browser-profile"
    browser_profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--disable-crash-reporter",
        "--disable-crashpad",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        f"--user-data-dir={str(browser_profile.resolve())}",
        f"--print-to-pdf={str(pdf_path.resolve())}",
        html_path.resolve().as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    shutil.rmtree(browser_profile, ignore_errors=True)
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "browser PDF export failed").strip()
        return False, message
    return True, f"PDF generated: {pdf_path}"


def count_pdf_pages(pdf_path: Path) -> int:
    if not pdf_path.exists():
        return 0
    data = pdf_path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page(?!s)", data))
