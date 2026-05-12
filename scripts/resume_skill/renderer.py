from __future__ import annotations

import html
import shutil
from dataclasses import dataclass
from pathlib import Path

from .jd_parser import JDAnalysis
from .retriever import ScoredExperience


CATEGORY_ORDER = ["education", "skill", "project", "internship", "work", "certification"]
CATEGORY_LABELS = {
    "education": "教育经历",
    "skill": "专业技能",
    "project": "项目经历",
    "internship": "实习经历",
    "work": "工作经历",
    "certification": "证书与资质",
}


@dataclass(frozen=True)
class RenderBudget:
    name: str
    density_class: str
    max_education: int = 2
    max_skill: int = 1
    max_certification: int = 0
    max_tailored: int = 4
    education_bullets: int = 1
    skill_bullets: int = 2
    regular_bullets: int = 2
    bullet_chars: int = 160
    compact_bullets: bool = True


FULL_BUDGET = RenderBudget(
    name="full",
    density_class="density-full",
    max_education=99,
    max_skill=99,
    max_certification=99,
    max_tailored=7,
    education_bullets=5,
    skill_bullets=5,
    regular_bullets=5,
    bullet_chars=0,
    compact_bullets=False,
)

ONE_PAGE_BUDGETS = [
    RenderBudget(name="one-page", density_class="density-one-page", max_tailored=7, regular_bullets=2, skill_bullets=2, bullet_chars=160),
    RenderBudget(name="tight", density_class="density-tight", max_tailored=6, regular_bullets=2, skill_bullets=1, bullet_chars=135),
    RenderBudget(name="ultra", density_class="density-ultra", max_tailored=5, regular_bullets=1, skill_bullets=1, bullet_chars=112),
    RenderBudget(name="minimum", density_class="density-minimum", max_tailored=3, regular_bullets=1, skill_bullets=1, bullet_chars=90),
]


def format_date(raw: object) -> str:
    if raw in (None, ""):
        return "至今"
    text = str(raw)
    parts = text.split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{parts[0]}.{parts[1]}"
    return text


def format_date_range(exp: dict) -> str:
    return f"{format_date(exp.get('date_start'))} - {format_date(exp.get('date_end'))}"


def one_page_budgets(max_tailored: int = 7) -> list[RenderBudget]:
    budgets: list[RenderBudget] = []
    for budget in ONE_PAGE_BUDGETS:
        budgets.append(RenderBudget(
            name=budget.name,
            density_class=budget.density_class,
            max_education=budget.max_education,
            max_skill=budget.max_skill,
            max_certification=budget.max_certification,
            max_tailored=min(budget.max_tailored, max_tailored),
            education_bullets=budget.education_bullets,
            skill_bullets=budget.skill_bullets,
            regular_bullets=budget.regular_bullets,
            bullet_chars=budget.bullet_chars,
            compact_bullets=budget.compact_bullets,
        ))
    return budgets


def selected_for_resume(
    results: list[ScoredExperience],
    max_tailored: int = 7,
    budget: RenderBudget | None = None,
) -> list[ScoredExperience]:
    active = budget or FULL_BUDGET
    education = [
        item for item in results
        if item.experience.get("category") == "education"
    ][:active.max_education]
    skills = [
        item for item in results
        if item.experience.get("category") == "skill"
    ][:active.max_skill]
    certifications = [
        item for item in results
        if item.experience.get("category") == "certification"
    ][:active.max_certification]
    tailored = [
        item for item in results
        if item.experience.get("category") not in {"education", "skill", "certification"}
    ][:min(active.max_tailored, max_tailored)]
    return education + skills + certifications + tailored


def group_results(results: list[ScoredExperience]) -> dict[str, list[ScoredExperience]]:
    grouped = {category: [] for category in CATEGORY_ORDER}
    for item in results:
        category = item.experience.get("category")
        if category in grouped:
            grouped[category].append(item)
    return grouped


def render_markdown(
    profile: dict,
    jd: JDAnalysis,
    results: list[ScoredExperience],
    budget: RenderBudget | None = None,
) -> str:
    active = budget or FULL_BUDGET
    name = clean_value(profile.get("name"), {"", "姓名"}) or "姓名"
    title = clean_value(profile.get("title"), {"", "求职意向 / 目标岗位", "目标岗位"}) or jd.job_title or "目标岗位"
    contact = [
        clean_value(profile.get("phone"), {"", "+86 13800000000"}),
        clean_value(profile.get("email"), {"", "name@example.com"}),
        clean_value(profile.get("location"), {""}),
    ]
    contact = [item for item in contact if item]

    lines = [f"# {name}", f"**{title}**"]
    if contact:
        lines.extend(["", " | ".join(contact)])
    lines.extend(["", "---", ""])

    for category, items in group_results(results).items():
        if not items:
            continue
        lines.extend([f"## {CATEGORY_LABELS.get(category, category)}", ""])
        for item in items:
            exp = item.experience
            heading = exp.get("title", "")
            subtitle = exp.get("subtitle", "")
            date_range = format_date_range(exp) if has_dates(exp) else ""
            if subtitle and date_range:
                lines.append(f"### {heading}")
                lines.append(f"**{subtitle}** · {date_range}")
            elif subtitle:
                lines.append(f"### {heading}")
                lines.append(f"**{subtitle}**")
            elif date_range:
                lines.append(f"### {heading} · {date_range}")
            else:
                lines.append(f"### {heading}")
            for bullet in experience_bullets(
                exp,
                max_bullets_for_category(category, active),
                active.compact_bullets,
                active.bullet_chars,
            ):
                lines.append(f"- {bullet}")
            lines.append("")

    if jd.keywords:
        lines.extend(["---", "", f"**关键词匹配**：{'、'.join(jd.keywords[:12])}", ""])
    return "\n".join(lines).strip() + "\n"


def render_html(
    profile: dict,
    jd: JDAnalysis,
    results: list[ScoredExperience],
    template_dir: Path,
    output_dir: Path,
    photo_path: Path | None = None,
    budget: RenderBudget | None = None,
) -> str:
    active = budget or FULL_BUDGET
    template = (template_dir / "template.html").read_text(encoding="utf-8")
    css = (template_dir / "style.css").read_text(encoding="utf-8")
    photo_html = render_photo(photo_path, output_dir)
    name = clean_value(profile.get("name"), {"", "姓名"}) or "姓名"
    title = clean_value(profile.get("title"), {"", "求职意向 / 目标岗位", "目标岗位"}) or jd.job_title or "目标岗位"
    contact_html = render_contact(profile)
    sections_html = render_sections_html(results, active)
    return (
        template
        .replace("{{ style_css }}", css)
        .replace("{{ name }}", html.escape(str(name)))
        .replace("{{ title }}", html.escape(str(title)))
        .replace("{{ contact_html }}", contact_html)
        .replace("{{ photo_html }}", photo_html)
        .replace("{{ sections_html }}", sections_html)
        .replace("{{ generated_at }}", "")
        .replace("{{ density_class }}", html.escape(active.density_class))
    )


def render_contact(profile: dict) -> str:
    rows: list[str] = []
    phone = clean_value(profile.get("phone"), {"", "+86 13800000000"})
    email = clean_value(profile.get("email"), {"", "name@example.com"})
    location = clean_value(profile.get("location"), {""})
    if phone:
        rows.append(f"<div><strong>电话：</strong>{html.escape(phone)}</div>")
    if email:
        rows.append(f"<div><strong>邮箱：</strong>{html.escape(email)}</div>")
    if location:
        rows.append(f"<div><strong>地点：</strong>{html.escape(location)}</div>")
    for link in profile.get("links") or []:
        rows.append(f"<div>{html.escape(str(link))}</div>")
    return "\n".join(rows)


def render_photo(photo_path: Path | None, output_dir: Path) -> str:
    if not photo_path or not photo_path.exists():
        return ""
    target = output_dir / f"photo{photo_path.suffix.lower() or '.png'}"
    if photo_path.resolve() != target.resolve():
        shutil.copy2(photo_path, target)
    return f'<img class="portrait" src="{html.escape(target.name)}" alt="photo">'


def render_sections_html(results: list[ScoredExperience], budget: RenderBudget) -> str:
    chunks: list[str] = []
    for category, items in group_results(results).items():
        if not items:
            continue
        chunks.append(f'<section class="resume-section {html.escape(category)}">')
        chunks.append(f"<h2>{html.escape(CATEGORY_LABELS.get(category, category))}</h2>")
        for item in items:
            chunks.append(render_experience_html(item.experience, category, budget))
        chunks.append("</section>")
    return "\n".join(chunks)


def render_experience_html(exp: dict, category: str, budget: RenderBudget) -> str:
    title = html.escape(str(exp.get("title", "")))
    subtitle = html.escape(str(exp.get("subtitle", "")))
    date_range = html.escape(format_date_range(exp)) if has_dates(exp) else ""
    location = html.escape(str(exp.get("location", "")))
    meta_bits = [bit for bit in [subtitle, location] if bit]
    meta = " · ".join(meta_bits)
    bullets = experience_bullets(
        exp,
        max_bullets_for_category(category, budget),
        budget.compact_bullets,
        budget.bullet_chars,
    )

    if category == "education":
        row = [
            '<div class="entry education-entry">',
            '<div class="entry-head grid-head">',
            f"<strong>{title}</strong>",
            f"<span>{meta}</span>",
            f"<span>{date_range}</span>",
            "</div>",
        ]
    else:
        row = [
            '<div class="entry">',
            '<div class="entry-head">',
            f"<strong>{title}</strong>",
            f"<span>{date_range}</span>" if date_range else "",
            "</div>",
        ]
        if meta:
            row.append(f'<div class="entry-meta">{meta}</div>')

    if bullets:
        row.append("<ul>")
        for bullet in bullets:
            row.append(f"<li>{format_bullet_html(bullet)}</li>")
        row.append("</ul>")
    row.append("</div>")
    return "\n".join(row)


def has_dates(exp: dict) -> bool:
    return bool(exp.get("date_start") or exp.get("date_end"))


def clean_value(raw: object, placeholders: set[str]) -> str:
    text = str(raw or "").strip()
    return "" if text in placeholders else text


def max_bullets_for_category(category: str, budget: RenderBudget) -> int:
    if category == "education":
        return budget.education_bullets
    if category == "skill":
        return budget.skill_bullets
    return budget.regular_bullets


def experience_bullets(
    exp: dict,
    max_bullets: int | None = None,
    compact: bool = False,
    max_chars: int = 0,
) -> list[str]:
    star = exp.get("star_details") or {}
    bullets: list[str] = []
    star_order = ("result", "action", "task", "situation") if compact else ("situation", "task", "action", "result")
    for key in star_order:
        text = str(star.get(key) or "").strip()
        if text:
            bullets.append(text)
    for metric in exp.get("metrics") or []:
        if isinstance(metric, dict) and metric.get("metric") and metric.get("value"):
            bullets.append(f"{metric['metric']}：{metric['value']}")
    if not bullets:
        bullets.extend(str(item) for item in (exp.get("highlights") or [])[:3])
    compacted = compact_bullets(bullets)
    if max_chars:
        compacted = [truncate_text(item, max_chars) for item in compacted]
    if max_bullets is None:
        return compacted
    return compacted[:max_bullets]


def truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    trimmed = text[:limit].rstrip(" ，,；;。")
    return f"{trimmed}..."


def compact_bullets(bullets: list[str]) -> list[str]:
    seen: set[str] = set()
    compacted: list[str] = []
    for bullet in bullets:
        text = " ".join(str(bullet).split())
        if text and text not in seen:
            seen.add(text)
            compacted.append(text)
    return compacted[:5]


def format_bullet_html(text: str) -> str:
    escaped = html.escape(text)
    for prefix in ["技术栈", "项目概述", "结果导向评估", "过程导向评估", "轨迹与成本监控"]:
        if escaped.startswith(prefix):
            return f"<strong>{prefix}</strong>{escaped[len(prefix):]}"
    if "：" in escaped and len(escaped.split("：", 1)[0]) <= 12:
        left, right = escaped.split("：", 1)
        return f"<strong>{left}：</strong>{right}"
    return escaped
