from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    ActivityTimeline,
    FilterPreset,
    Followup,
    Lead,
    LeadDocument,
    Note,
    Tag,
)


@admin.register(FilterPreset)
class FilterPresetAdmin(ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class FollowupInline(TabularInline):
    model = Followup
    extra = 1
    tab = True


class ActivityTimelineInline(TabularInline):
    model = ActivityTimeline
    tab = True
    extra = 0
    show_in_index = False


class NoteInline(TabularInline):
    model = Note
    tab = True
    extra = 0
    show_in_index = False


class LeadDocumentInline(TabularInline):
    model = LeadDocument
    tab = True
    extra = 0
    show_in_index = False


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
    inlines = [FollowupInline, ActivityTimelineInline, NoteInline, LeadDocumentInline]


@admin.register(Note)
class NoteAdmin(ModelAdmin):
    list_display = ("lead", "created_by", "created_at")
    search_fields = ("content", "lead__full_name")
