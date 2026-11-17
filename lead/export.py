from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable

from django.db.models import F, Prefetch
from django.utils import timezone

from .models import Followup, Lead


@dataclass(frozen=True)
class ExportColumn:
    label: str
    value: Callable[[Lead], object]
    select: tuple = field(default_factory=tuple)
    prefetch: tuple = field(default_factory=tuple)


def _user_name(user):
    if not user:
        return ""
    return user.get_full_name().strip() or user.username


def _date(value):
    return value.strftime("%Y-%m-%d") if value else ""


def _datetime(value):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%Y-%m-%d %H:%M")


def _time(value):
    return value.strftime("%H:%M") if value else ""


def _followups(lead):
    return list(lead.followups.all())


def _next_followup(lead):
    followups = _followups(lead)
    for followup in followups:
        if followup.status == "pending":
            return followup
    return followups[0] if followups else None


def _last_followup(lead):
    for followup in reversed(_followups(lead)):
        if followup.followup_date:
            return followup
    return None


def _last_activity(lead):
    return lead.activities.first()


EXPORT_COLUMNS = OrderedDict([
    ("id", ExportColumn("ID", lambda lead: lead.id)),
    ("full_name", ExportColumn("Full Name", lambda lead: lead.full_name)),
    ("email", ExportColumn("Email", lambda lead: lead.email or "")),
    ("phone_number", ExportColumn("Phone Number", lambda lead: lead.phone_number)),
    ("source", ExportColumn("Source", lambda lead: lead.source or "")),
    ("status", ExportColumn("Status", lambda lead: lead.get_status_display())),
    ("estimate_value", ExportColumn("Estimate Value", lambda lead: lead.estimate_value or "")),
    ("rating", ExportColumn("Rating", lambda lead: lead.rating)),
    ("tags", ExportColumn(
        "Tags",
        lambda lead: ", ".join(tag.name for tag in lead.tags.all()),
        prefetch=("tags",),
    )),
    ("assigned_to", ExportColumn(
        "Assigned To",
        lambda lead: _user_name(lead.assigned_to),
        select=("assigned_to",),
    )),
    ("created_by", ExportColumn(
        "Created By",
        lambda lead: _user_name(lead.created_by),
        select=("created_by",),
    )),
    ("created_at", ExportColumn("Created At", lambda lead: _datetime(lead.created_at))),
    ("updated_at", ExportColumn("Updated At", lambda lead: _datetime(lead.updated_at))),
    ("summary", ExportColumn("Summary", lambda lead: lead.summary or "")),
    ("next_followup_date", ExportColumn(
        "Next Follow-up Date",
        lambda lead: _date(_next_followup(lead).followup_date) if _next_followup(lead) else "",
        prefetch=("followups",),
    )),
    ("next_followup_time", ExportColumn(
        "Next Follow-up Time",
        lambda lead: _time(_next_followup(lead).followup_time) if _next_followup(lead) else "",
        prefetch=("followups",),
    )),
    ("last_followup_date", ExportColumn(
        "Last Follow-up Date",
        lambda lead: _date(_last_followup(lead).followup_date) if _last_followup(lead) else "",
        prefetch=("followups",),
    )),
    ("pending_followup_count", ExportColumn(
        "Pending Follow-ups",
        lambda lead: sum(1 for followup in _followups(lead) if followup.status == "pending"),
        prefetch=("followups",),
    )),
    ("last_activity_type", ExportColumn(
        "Last Activity Type",
        lambda lead: _last_activity(lead).get_activity_type_display() if _last_activity(lead) else "",
        prefetch=("activities",),
    )),
    ("last_activity_note", ExportColumn(
        "Last Activity Note",
        lambda lead: (
            _last_activity(lead).description.get("note_content", "")
            if _last_activity(lead) and _last_activity(lead).activity_type == "note_added"
            else ""
        ),
        prefetch=("activities",),
    )),
])

DEFAULT_COLUMNS = [
    "full_name",
    "email",
    "phone_number",
    "status",
    "source",
    "tags",
    "assigned_to",
    "created_at",
    "next_followup_date",
]

FOLLOWUP_PREFETCH = Prefetch(
    "followups",
    queryset=Followup.objects.order_by(
        F("followup_date").asc(nulls_last=True),
        F("followup_time").asc(nulls_last=True),
        "-id",
    ),
)


def prepare_queryset(queryset, column_keys):
    select = set()
    prefetch = set()
    for key in column_keys:
        column = EXPORT_COLUMNS[key]
        select.update(column.select)
        prefetch.update(column.prefetch)

    if select:
        queryset = queryset.select_related(*sorted(select))
    for name in sorted(prefetch):
        queryset = queryset.prefetch_related(
            FOLLOWUP_PREFETCH if name == "followups" else name
        )
    return queryset


def sanitize_cell(value):
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text
