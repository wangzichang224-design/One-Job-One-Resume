"""Small rule-based JD parser used before experience retrieval."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class HardRequirement:
    requirement: str
    must_have: bool = True


@dataclass
class JDAnalysis:
    job_title: str = ""
    company: str = ""
    hard_requirements: list[HardRequirement] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "job_title": self.job_title,
            "company": self.company,
            "hard_requirements": [
                {"requirement": item.requirement, "must_have": item.must_have}
                for item in self.hard_requirements
            ],
            "soft_skills": self.soft_skills,
            "keywords": self.keywords,
            "pain_points": self.pain_points,
            "weights": self.weights,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


_HARD_REQUIREMENT_PATTERNS: list[tuple[str, bool]] = [
    (r"(硕士|研究生|博士|本科|统招本科)", True),
    (r"(英语|CET[46]|雅思|托福|日语|N1|N2)", False),
    (r"(Python|SQL|Excel|Tableau|Power BI|Axure|Figma|Java|C\+\+|Go|Docker|Git)", True),
    (r"(LLM|AIGC|AI|NLP|机器学习|深度学习|数据分析|数据挖掘|Agent|RAG)", False),
    (r"(审计|会计|财务分析|跨境电商|用户运营|活动运营|内容运营|产品经理)", False),
    (r"(\d+\+?\s*年.*经验|实习.*经验|项目.*经验|产品.*经验|运营.*经验)", True),
]

_SOFT_SKILL_PATTERNS: list[str] = [
    r"(沟通|协作|团队|合作|逻辑|分析|学习|自驱|owner|ownership)",
    r"(抗压|执行力|推动|落地|细节|责任心|创新|主动)",
]

_KEYWORDS: dict[str, list[str]] = {
    "技术": ["Python", "SQL", "LLM", "AIGC", "Agent", "RAG", "NLP", "API", "算法", "架构", "开发", "Docker", "Git"],
    "产品": ["产品", "需求", "PRD", "原型", "Axure", "用户", "增长", "迭代", "roadmap", "商业化"],
    "数据": ["数据分析", "数据驱动", "指标", "A/B测试", "报表", "数据挖掘", "可视化"],
    "运营": ["运营", "活动", "内容", "用户增长", "私域", "社群", "新媒体", "跨境电商", "KOL"],
    "财务": ["审计", "底稿", "会计", "财报", "年审", "内控", "风险"],
    "游戏": ["游戏", "小游戏", "Cocos", "Unity", "玩法", "数值", "发行"],
}


def parse_jd(jd_text: str, job_title: str | None = None, company: str | None = None) -> JDAnalysis:
    analysis = JDAnalysis(job_title=job_title or _extract_job_title(jd_text), company=company or "")

    seen: set[str] = set()
    for pattern, must_have in _HARD_REQUIREMENT_PATTERNS:
        for match in re.finditer(pattern, jd_text, re.IGNORECASE):
            text = match.group(0).strip()
            key = text.lower()
            if text and key not in seen:
                seen.add(key)
                analysis.hard_requirements.append(HardRequirement(text, must_have))

    seen_soft: set[str] = set()
    for pattern in _SOFT_SKILL_PATTERNS:
        for match in re.finditer(pattern, jd_text, re.IGNORECASE):
            text = match.group(0).strip()
            key = text.lower()
            if text and key not in seen_soft:
                seen_soft.add(key)
                analysis.soft_skills.append(text)

    seen_kw: set[str] = set()
    lower_text = jd_text.lower()
    for words in _KEYWORDS.values():
        for word in words:
            if word.lower() in lower_text and word not in seen_kw:
                seen_kw.add(word)
                analysis.keywords.append(word)

    analysis.pain_points = _extract_pain_points(jd_text)
    analysis.weights = _infer_weights(analysis)
    return analysis


def _extract_job_title(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:8]:
        match = re.search(r"(招聘|职位|岗位|职务|名称)[：:]\s*(.+)", line)
        if match:
            return match.group(2).strip()[:50]
        if 2 < len(line) <= 40 and not re.search(r"[。；;]", line):
            if any(word in line for word in ["产品", "运营", "数据", "AI", "AIGC", "实习", "经理", "开发"]):
                return line
    return ""


def _extract_pain_points(text: str) -> list[str]:
    points: list[str] = []
    for keyword in ["痛点", "挑战", "问题", "难点", "目标", "职责"]:
        pattern = rf"{keyword}[：:]\s*([^。\n]+)"
        for match in re.finditer(pattern, text):
            points.append(match.group(1).strip())
    if not points:
        for match in re.finditer(r"(负责|提升|优化|搭建|推进|分析|解决)\s*([^，。\n]{4,36})", text):
            points.append(match.group(0).strip())
            if len(points) >= 5:
                break
    return points[:5]


def _infer_weights(analysis: JDAnalysis) -> dict[str, float]:
    weights = {
        "tag_match": 0.30,
        "hard_requirement": 0.25,
        "industry_relevance": 0.20,
        "evidence_quality": 0.10,
        "recency": 0.15,
    }
    kws = {item.lower() for item in analysis.keywords}
    if kws & {"llm", "aigc", "agent", "rag", "python", "算法", "开发"}:
        weights.update({"tag_match": 0.35, "hard_requirement": 0.30, "industry_relevance": 0.15, "recency": 0.10})
    if kws & {"审计", "底稿", "会计", "财报", "内控"}:
        weights.update({"industry_relevance": 0.30, "tag_match": 0.25, "evidence_quality": 0.15})
    if kws & {"运营", "活动", "内容", "用户增长", "跨境电商"}:
        weights.update({"industry_relevance": 0.25, "tag_match": 0.30, "recency": 0.20})
    return weights
