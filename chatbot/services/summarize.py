import re

from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone

from lead.models import Lead

from .ollama_service import chat

SYSTEM_PROMPT = (
    "You are an internal assistant for a sales CRM. Summarize the lead described below "
    "using its information, notes, and follow-ups. The notes may be written in English "
    "or Nepali. Never invent details that are not present in the data.\n\n"
    "Structure your reply in exactly two parts:\n"
    "1. A concise summary of the lead covering its profile (status, source, estimate "
    "value, rating), notes, and follow-ups.\n"
    "2. A section titled '### Recommended Next Action' containing ONLY a single mermaid "
    "flowchart code block (```mermaid ... ```) that visualizes the recommended next "
    "steps as a top-to-bottom flowchart. Rules for the flowchart:\n"
    "- Start with the first action the sales rep should take.\n"
    "- Use short node labels of at most 5 words each.\n"
    "- Branch where alternative paths make sense; end with recording the outcome in "
    "the CRM and updating the lead status/rating.\n"
    "- Use valid mermaid 'flowchart TD' syntax with quoted labels and no prose inside "
    "the code block."
)

MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def split_summary_and_flowchart(text):
    """Separate the prose summary from the mermaid next-action flowchart."""
    match = MERMAID_BLOCK_RE.search(text)
    if not match:
        return text.strip(), None
    flowchart = match.group(1).strip()
    summary = (text[: match.start()] + text[match.end() :]).strip()
    summary = re.sub(r"\n{3,}", "\n\n", summary).strip()
    return summary, flowchart


def summarize_lead(lead_id, force_refresh=False):
    lead = get_object_or_404(Lead, id=lead_id)

    if not force_refresh and _summary_is_fresh(lead):
        return split_summary_and_flowchart(lead.summary)

    raw = _generate_summary(lead)
    lead.summary = raw
    lead.summary_generated_at = timezone.now()
    lead.save(update_fields=["summary", "summary_generated_at"])
    return split_summary_and_flowchart(raw)


def _summary_is_fresh(lead):
    if not lead.summary or not lead.summary_generated_at:
        return False
    return lead.summary_generated_at >= _latest_change(lead)


def _latest_change(lead):
    timestamps = [
        lead.updated_at,
        lead.notes.aggregate(latest=Max("updated_at"))["latest"],
        lead.followups.aggregate(latest=Max("updated_at"))["latest"],
        lead.documents.aggregate(latest=Max("updated_at"))["latest"],
        lead.activities.aggregate(latest=Max("created_at"))["latest"],
    ]
    return max(t for t in timestamps if t is not None)


def _generate_summary(lead):
    notes_text = "\n".join(
        f"- [{note.created_at:%Y-%m-%d}] {note.content}" for note in lead.notes.all()
    )
    followups_text = "\n".join(
        f"- [{f.followup_date}] ({f.status}) {f.notes}" for f in lead.followups.all()
    )

    lead_context = (
        f"Lead: {lead.full_name}\n"
        f"Status: {lead.status}\n"
        f"Source: {lead.source}\n"
        f"Estimate value: {lead.estimate_value}\n"
        f"Rating: {lead.rating}/10\n\n"
        f"Notes:\n{notes_text or 'No notes yet.'}\n\n"
        f"Follow-ups:\n{followups_text or 'No follow-ups yet.'}"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": lead_context},
    ]
    result = chat(messages)
    return result["message"]["content"]

    