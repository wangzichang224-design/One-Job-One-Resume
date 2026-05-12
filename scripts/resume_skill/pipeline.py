from __future__ import annotations

import json
import shutil
from pathlib import Path

from .jd_parser import parse_jd
from .paths import resolve_experiences, resolve_profile, resolve_template, timestamped_output_dir
from .pdf import count_pdf_pages, html_to_pdf
from .renderer import FULL_BUDGET, one_page_budgets, render_html, render_markdown, selected_for_resume
from .retriever import load_experiences, retrieve


def read_json(path: Path | None, default: object) -> object:
    if not path or not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_photo(profile: dict, explicit: str | None = None) -> Path | None:
    raw = explicit or profile.get("photo")
    if not raw:
        return None
    path = Path(str(raw)).expanduser()
    candidates = [
        path,
        Path.cwd() / path,
        Path.cwd() / "data" / path.name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_resume(
    jd_text: str,
    *,
    experiences_path: str | None = None,
    profile_path: str | None = None,
    photo_path: str | None = None,
    template: str = "classic_zh",
    output_dir: str | None = None,
    title: str | None = None,
    company: str | None = None,
    role: str | None = None,
    min_score: float = 0.0,
    max_tailored: int = 7,
    one_page: bool = True,
    make_pdf: bool = False,
    source_image: str | None = None,
    profile_overrides: dict | None = None,
) -> dict:
    out_dir = Path(output_dir) if output_dir else timestamped_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    exp_path = resolve_experiences(experiences_path)
    if not exp_path:
        raise FileNotFoundError("No experience database found. Run `python -m resume_skill init` first.")
    profile_file = resolve_profile(profile_path)
    profile = read_json(profile_file, {})
    if not isinstance(profile, dict):
        raise ValueError("Profile JSON must be an object.")
    if profile_overrides:
        profile.update({key: value for key, value in profile_overrides.items() if value})

    experiences = load_experiences(exp_path)
    jd = parse_jd(jd_text, job_title=title, company=company)
    results = retrieve(jd, experiences, target_role_filter=role, min_score=min_score)
    write_json(out_dir / "jd_analysis.json", jd.to_dict())
    (out_dir / "jd_text.md").write_text(jd_text, encoding="utf-8")
    write_json(out_dir / "selected_experiences.json", [
        {
            "id": item.experience.get("id"),
            "score": round(item.score, 4),
            "match_details": item.match_details,
            "experience": item.experience,
        }
        for item in results
    ])

    if source_image:
        image = Path(source_image)
        if image.exists():
            shutil.copy2(image, out_dir / f"jd_image{image.suffix.lower()}")

    template_dir = resolve_template(template)
    photo = resolve_photo(profile, photo_path)
    budgets = one_page_budgets(max_tailored) if one_page else [FULL_BUDGET]
    if not make_pdf:
        budgets = budgets[:1]

    rendered_count = 0
    final_budget = budgets[0].name
    pdf_message = ""
    pdf_pages = 0
    pdf_path = None

    for index, budget in enumerate(budgets):
        resume_results = selected_for_resume(results, max_tailored=max_tailored, budget=budget)
        rendered_count = len(resume_results)
        final_budget = budget.name
        markdown = render_markdown(profile, jd, resume_results, budget=budget)
        html = render_html(profile, jd, resume_results, template_dir, out_dir, photo, budget=budget)
        (out_dir / "draft_resume.md").write_text(markdown, encoding="utf-8")
        (out_dir / "resume.html").write_text(html, encoding="utf-8")
        write_json(out_dir / "rendered_experiences.json", [
            {
                "id": item.experience.get("id"),
                "score": round(item.score, 4),
                "category": item.experience.get("category"),
                "title": item.experience.get("title"),
                "budget": budget.name,
            }
            for item in resume_results
        ])

        if not make_pdf:
            break

        candidate_pdf = out_dir / "resume.pdf"
        ok, pdf_message = html_to_pdf(out_dir / "resume.html", candidate_pdf)
        if not ok:
            pdf_path = None
            break

        pdf_pages = count_pdf_pages(candidate_pdf)
        pdf_path = candidate_pdf
        if not one_page or pdf_pages <= 1 or index == len(budgets) - 1:
            break
        candidate_pdf.unlink(missing_ok=True)

    return {
        "output_dir": str(out_dir.resolve()),
        "jd_analysis": str((out_dir / "jd_analysis.json").resolve()),
        "selected_experiences": str((out_dir / "selected_experiences.json").resolve()),
        "draft_resume": str((out_dir / "draft_resume.md").resolve()),
        "resume_html": str((out_dir / "resume.html").resolve()),
        "resume_pdf": str(pdf_path.resolve()) if pdf_path else "",
        "pdf_message": pdf_message,
        "pdf_pages": pdf_pages,
        "experience_count": len(experiences),
        "selected_count": len(results),
        "rendered_count": rendered_count,
        "render_budget": final_budget,
    }
