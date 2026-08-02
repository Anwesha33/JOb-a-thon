"""Turn an uploaded resume file into a structured Profile.

Deliberately heuristic and dependency-light: extract raw text, then pull
out contact details, a likely headline, and skills. Anything it misses
the user can fix in the UI, so we favour "useful and fast" over "perfect".
"""
from __future__ import annotations

import io
import re

from ..models import Profile
from .experience import estimate_years

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Fairly permissive international-ish phone matcher.
PHONE_RE = re.compile(r"(?:(?:\+|00)\d{1,3}[\s-]?)?(?:\d[\s-]?){9,12}\d")
URL_RE = re.compile(r"https?://\S+|www\.\S+|linkedin\.com/\S+", re.I)

# A pragmatic, extensible skill vocabulary. This is only used to *recognise*
# skills mentioned anywhere in the resume; the explicit "Skills" section
# (parsed separately) catches everything else.
KNOWN_SKILLS = {
    # languages
    "python", "java", "javascript", "typescript", "go", "golang", "c++", "c#",
    "kotlin", "swift", "ruby", "php", "scala", "rust", "sql", "r", "matlab",
    # web / frameworks
    "react", "angular", "vue", "node", "node.js", "express", "django", "flask",
    "fastapi", "spring", "spring boot", "next.js", "redux", "html", "css",
    "tailwind", "graphql", "rest", "grpc",
    # data / ml
    "pandas", "numpy", "pytorch", "tensorflow", "scikit-learn", "spark",
    "hadoop", "kafka", "airflow", "machine learning", "deep learning", "nlp",
    "data analysis", "data science", "tableau", "power bi", "excel",
    # infra / cloud
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "jenkins",
    "ci/cd", "linux", "git", "microservices", "redis", "postgresql", "mysql",
    "mongodb", "elasticsearch",
    # general / soft
    "agile", "scrum", "product management", "project management",
    "communication", "leadership", "problem solving", "stakeholder management",
}

# Section headers that usually precede a role/title line.
HEADLINE_HINTS = (
    "engineer", "developer", "manager", "analyst", "designer", "scientist",
    "consultant", "lead", "architect", "intern", "associate", "specialist",
    "director", "administrator", "officer", "executive",
)

SKILLS_SECTION_RE = re.compile(
    r"(?:technical\s+)?skills?\s*[:\n]", re.I
)
_SECTION_BREAK_RE = re.compile(
    r"\n\s*(experience|education|projects?|work|employment|certifications?|"
    r"achievements?|summary|objective)\b",
    re.I,
)


def extract_text(filename: str, data: bytes) -> str:
    """Extract plain text from a PDF, DOCX, or TXT upload."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _extract_pdf(data)
    if lower.endswith(".docx"):
        return _extract_docx(data)
    if lower.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="ignore")
    raise ValueError(
        f"Unsupported file type: {filename!r}. Use PDF, DOCX, or TXT."
    )


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _extract_docx(data: bytes) -> str:
    import docx  # python-docx

    document = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs)


def parse_resume(filename: str, data: bytes) -> Profile:
    """Full pipeline: bytes -> Profile."""
    text = extract_text(filename, data)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    email = _first(EMAIL_RE.findall(text))
    phone = _clean_phone(_first(PHONE_RE.findall(text)))
    name = _guess_name(lines, email)
    headline = _guess_headline(lines)
    skills = _extract_skills(text)

    return Profile(
        source_filename=filename,
        name=name,
        email=email,
        phone=phone,
        headline=headline,
        experience_years=estimate_years(text),
        roles=[headline] if headline else [],
        skills=skills,
        summary=None,
        raw_text=text,
    )


def _first(items: list[str]) -> str | None:
    return items[0].strip() if items else None


def _clean_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"[^\d+]", "", raw)
    # Reject obvious false positives (e.g. a long ID or a year run-on).
    if len(re.sub(r"\D", "", digits)) < 10:
        return None
    return digits


def _guess_name(lines: list[str], email: str | None) -> str | None:
    """The name is usually the first short, title-ish line with no digits."""
    for line in lines[:6]:
        if EMAIL_RE.search(line) or URL_RE.search(line):
            continue
        if any(ch.isdigit() for ch in line):
            continue
        words = line.split()
        if 1 < len(words) <= 4 and all(w[0].isupper() for w in words if w):
            return line
    return None


def _guess_headline(lines: list[str]) -> str | None:
    for line in lines[:12]:
        low = line.lower()
        if any(hint in low for hint in HEADLINE_HINTS) and len(line) <= 80:
            return line
    return None


def _extract_skills(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    # 1) Anything from a dedicated Skills section.
    match = SKILLS_SECTION_RE.search(text)
    if match:
        tail = text[match.end():]
        end = _SECTION_BREAK_RE.search(tail)
        section = tail[: end.start()] if end else tail[:600]
        for token in re.split(r"[,\n•|/·;]+", section):
            token = token.strip(" \t-–—:")
            if 1 < len(token) <= 40 and not token.lower().startswith("skill"):
                key = token.lower()
                if key not in seen:
                    seen.add(key)
                    found.append(token)

    # 2) Known skills mentioned anywhere (catches resumes with no section).
    low_text = text.lower()
    for skill in KNOWN_SKILLS:
        if re.search(r"(?<![a-z])" + re.escape(skill) + r"(?![a-z])", low_text):
            if skill not in seen:
                seen.add(skill)
                found.append(skill)

    return found[:40]
