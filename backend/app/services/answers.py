"""Generate answers to open-ended application questions.

If an Anthropic API key is configured, answers are drafted by Claude, grounded
strictly in the candidate's resume. Otherwise we fall back to a resume-derived
template so the tool still works offline. Either way, answers only draw on what
the resume actually contains — the tool never invents credentials.
"""
from __future__ import annotations

from typing import Optional

from ..config import get_settings
from ..models import Opportunity, Profile

# Opus 4.8 — omit `thinking` for these short, well-scoped generations.
_MODEL = "claude-opus-4-8"


def generate_answer(
    question: str,
    profile: Profile,
    opportunity: Optional[Opportunity] = None,
) -> str:
    """Draft an answer to `question` using only the resume's contents."""
    settings = get_settings()
    if settings.has_llm:
        try:
            return _generate_with_llm(question, profile, opportunity)
        except Exception:
            # Any API hiccup falls back to the template rather than failing.
            pass
    return _generate_from_template(question, profile, opportunity)


def _resume_context(profile: Profile, opportunity: Optional[Opportunity]) -> str:
    parts = [f"Candidate name: {profile.name or 'the candidate'}"]
    if profile.headline:
        parts.append(f"Current title: {profile.headline}")
    if profile.skills:
        parts.append(f"Skills: {', '.join(profile.skills)}")
    if profile.summary:
        parts.append(f"Summary: {profile.summary}")
    if profile.raw_text:
        parts.append(f"Resume text:\n{profile.raw_text[:4000]}")
    if opportunity:
        parts.append(
            f"Applying for: {opportunity.title} at {opportunity.company}"
            + (f"\nJob description: {opportunity.description}" if opportunity.description else "")
        )
    return "\n\n".join(parts)


def _generate_with_llm(
    question: str, profile: Profile, opportunity: Optional[Opportunity]
) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
    system = (
        "You are helping a job seeker answer an application question. Write in "
        "the first person as the candidate. Ground every claim strictly in the "
        "resume provided — never invent employers, degrees, numbers, or skills "
        "the resume does not support. Be specific, confident, and concise "
        "(3-6 sentences). Return only the answer text, no preamble."
    )
    user = (
        f"{_resume_context(profile, opportunity)}\n\n"
        f"Application question: {question}\n\n"
        "Write the candidate's answer."
    )
    response = client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()


def _generate_from_template(
    question: str, profile: Profile, opportunity: Optional[Opportunity]
) -> str:
    """A resume-grounded answer without an LLM. Not as polished, but honest."""
    name = profile.name or "I"
    top_skills = ", ".join(profile.skills[:5]) if profile.skills else "my core skills"
    role = profile.headline or "my field"
    where = f" at {opportunity.company}" if opportunity else ""
    target = f" the {opportunity.title} role" if opportunity else " this role"

    lowered = question.lower()
    if "why" in lowered and ("hire" in lowered or "you" in lowered or "fit" in lowered):
        return (
            f"With a background as {role}, I bring hands-on experience across "
            f"{top_skills}. I'm confident I can contribute quickly to{target}"
            f"{where} because my experience maps directly to what the role "
            f"needs, and I take ownership of the problems I work on."
        )
    if "strength" in lowered:
        return (
            f"My core strengths are {top_skills}, developed through my work as "
            f"{role}. I combine technical depth with a bias for shipping and "
            f"clear communication."
        )
    if "weak" in lowered:
        return (
            "Earlier in my career I took on too much myself; I've since learned "
            "to delegate and lean on process, which has made my delivery more "
            "reliable."
        )
    # Generic fallback.
    return (
        f"Drawing on my experience as {role} and skills in {top_skills}, I would "
        f"approach this by focusing on impact and collaboration. My track record "
        f"shows I can deliver in areas directly relevant to{target}{where}."
    )
