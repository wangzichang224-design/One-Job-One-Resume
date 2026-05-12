"""Score verified experiences against a parsed JD."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .jd_parser import JDAnalysis


@dataclass(order=True)
class ScoredExperience:
    score: float = field(compare=True)
    experience: dict = field(compare=False)
    match_details: dict = field(default_factory=dict, compare=False)


def load_json(path: Path) -> object:
    text = path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(repair_inner_quotes(text))


def repair_inner_quotes(text: str) -> str:
    """Escape quote characters that appear inside a JSON string value.

    This is intentionally small and conservative. It helps with hand-edited
    Chinese resume databases such as: "这是一个"关键词"描述".
    """
    out: list[str] = []
    in_string = False
    escaped = False
    length = len(text)
    for index, char in enumerate(text):
        if not in_string:
            out.append(char)
            if char == '"':
                in_string = True
            continue

        if escaped:
            out.append(char)
            escaped = False
            continue
        if char == "\\":
            out.append(char)
            escaped = True
            continue
        if char == '"':
            next_char = _next_non_space(text, index + 1, length)
            if next_char in {":", ",", "}", "]", ""}:
                out.append(char)
                in_string = False
            else:
                out.append('\\"')
            continue
        out.append(char)
    return "".join(out)


def _next_non_space(text: str, start: int, length: int) -> str:
    cursor = start
    while cursor < length and text[cursor].isspace():
        cursor += 1
    return text[cursor] if cursor < length else ""


def load_experiences(path: Path) -> list[dict]:
    data = load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Experience database must be a JSON array: {path}")
    return [item for item in data if isinstance(item, dict)]


def retrieve(
    jd: JDAnalysis,
    experiences: list[dict],
    target_role_filter: str | None = None,
    min_score: float = 0.0,
) -> list[ScoredExperience]:
    safe_experiences = [item for item in experiences if not item.get("needs_verification", False)]

    if target_role_filter:
        safe_experiences = [
            item for item in safe_experiences
            if target_role_filter in (item.get("target_roles") or [])
            or "*" in (item.get("target_roles") or [])
        ]

    results: list[ScoredExperience] = []
    for exp in safe_experiences:
        score, details = _score_experience(exp, jd)
        if score >= min_score:
            results.append(ScoredExperience(score=score, experience=exp, match_details=details))

    results.sort(key=lambda item: item.score, reverse=True)
    return results


def _score_experience(exp: dict, jd: JDAnalysis) -> tuple[float, dict]:
    weights = jd.weights or {}
    tag_score = _tag_match(exp.get("tags") or [], jd.keywords)
    hard_score = _hard_requirement_match(exp, jd)
    industry_score = _industry_relevance(exp, jd)
    evidence_score = _evidence_quality(exp)
    recency_score = _recency(exp)
    total = (
        weights.get("tag_match", 0.30) * tag_score
        + weights.get("hard_requirement", 0.25) * hard_score
        + weights.get("industry_relevance", 0.20) * industry_score
        + weights.get("evidence_quality", 0.10) * evidence_score
        + weights.get("recency", 0.15) * recency_score
    )
    details = {
        "tag_match": round(tag_score, 3),
        "hard_requirement": round(hard_score, 3),
        "industry_relevance": round(industry_score, 3),
        "evidence_quality": round(evidence_score, 3),
        "recency": round(recency_score, 3),
        "total": round(total, 3),
    }
    return total, details


def _tag_match(exp_tags: list[str], jd_keywords: list[str]) -> float:
    if not exp_tags or not jd_keywords:
        return 0.0
    tags = {str(item).lower().strip() for item in exp_tags}
    kws = {str(item).lower().strip() for item in jd_keywords}
    if not tags:
        return 0.0
    exact = len(tags & kws) / len(tags)
    fuzzy = sum(1 for tag in tags if any(tag in kw or kw in tag for kw in kws)) / len(tags)
    return min(max(exact, fuzzy), 1.0)


def _hard_requirement_match(exp: dict, jd: JDAnalysis) -> float:
    if not jd.hard_requirements:
        return 1.0
    exp_text = json.dumps(exp, ensure_ascii=False).lower()
    matched = 0
    must_have_missed = False
    for requirement in jd.hard_requirements:
        keyword = requirement.requirement.lower()
        if keyword in exp_text:
            matched += 1
        elif requirement.must_have:
            must_have_missed = True
    base = matched / len(jd.hard_requirements)
    return base * 0.35 if must_have_missed else base


def _industry_relevance(exp: dict, jd: JDAnalysis) -> float:
    text = json.dumps(exp, ensure_ascii=False).lower()
    if not jd.keywords:
        return 0.5 if "*" in (exp.get("target_roles") or []) else 0.3
    matched = sum(1 for keyword in jd.keywords if keyword.lower() in text)
    score = matched / len(jd.keywords)
    title = jd.job_title.lower()
    for role in exp.get("target_roles") or []:
        role_lower = str(role).lower()
        if role_lower == "*":
            score = max(score, 0.65)
        elif role_lower and (role_lower in title or title in role_lower):
            score = max(score, 0.8)
    return min(score, 1.0)


def _evidence_quality(exp: dict) -> float:
    level = exp.get("evidence_level", "")
    base = {"verified": 1.0, "plausible": 0.65, "anecdotal": 0.35}.get(level, 0.55)
    metrics = exp.get("metrics") or []
    if any(isinstance(item, dict) and item.get("verified") for item in metrics):
        base += 0.10
    return min(base, 1.0)


def _recency(exp: dict) -> float:
    raw = exp.get("date_end") or exp.get("date_start")
    if not raw:
        return 0.5
    try:
        year, month = [int(part) for part in str(raw).split("-")[:2]]
        end = date(year, month, 1)
    except (ValueError, TypeError):
        return 0.5
    today = date.today()
    months = (today.year - end.year) * 12 + today.month - end.month
    if months <= 3:
        return 1.0
    if months <= 6:
        return 0.9
    if months <= 12:
        return 0.75
    if months <= 24:
        return 0.55
    return 0.35
