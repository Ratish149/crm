from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Answer,
    Category,
    LeadResponse,
    LeadStageAnalysis,
    Question,
    SalesStage,
)


@admin.register(SalesStage)
class SalesStageAdmin(ModelAdmin):
    list_display = ("name", "order")
    ordering = ("order",)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name",)


class AnswerInline(TabularInline):
    model = Answer
    extra = 1
    tab = True


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ("text", "stage", "category", "question_type", "order")
    list_filter = ("stage", "category", "question_type")
    inlines = [AnswerInline]
    ordering = ("stage", "order")


@admin.register(Answer)
class AnswerAdmin(ModelAdmin):
    list_display = ("text", "question", "category")
    list_filter = ("question__stage", "category")


@admin.register(LeadResponse)
class LeadResponseAdmin(ModelAdmin):
    list_display = ("lead", "question", "get_selected_answers", "created_at")
    list_filter = ("lead", "question__stage")

    def get_selected_answers(self, obj):
        return ", ".join([a.text for a in obj.selected_answers.all()])

    get_selected_answers.short_description = "Selected Answers"


@admin.register(LeadStageAnalysis)
class LeadStageAnalysisAdmin(ModelAdmin):
    list_display = ("lead", "stage", "created_at")
    list_filter = ("stage",)
    readonly_fields = ("created_at",)
