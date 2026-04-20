from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    ActivityTimeline,
    Lead,
    Note,
    Tag,
)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "status",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "source", "assigned_to")
    search_fields = ("full_name", "email")


@admin.register(Note)
class NoteAdmin(ModelAdmin):
    list_display = ("lead", "created_by", "created_at")
    search_fields = ("content", "lead__full_name")


@admin.register(ActivityTimeline)
class ActivityTimelineAdmin(ModelAdmin):
    list_display = ("lead", "activity_type", "user", "created_at")
    list_filter = ("activity_type", "created_at")
