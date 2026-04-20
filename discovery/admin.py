from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    DiscoveryCategory,
    DiscoveryOption,
    DiscoveryQuestion,
    LeadDiscoveryAnswer,
)

# Register your models here.


@admin.register(DiscoveryCategory)
class DiscoveryCategoryAdmin(ModelAdmin):
    list_display = ("name", "created_at")


class DiscoveryOptionInline(TabularInline):
    model = DiscoveryOption
    fields = ("category", "text", "description")
    tab = True
    extra = 1


@admin.register(DiscoveryQuestion)
class DiscoveryQuestionAdmin(ModelAdmin):
    list_display = ("title", "created_at")
    inlines = [DiscoveryOptionInline]


@admin.register(LeadDiscoveryAnswer)
class LeadDiscoveryAnswerAdmin(ModelAdmin):
    list_display = ("lead", "question", "get_options", "created_at")
    list_filter = ("lead", "question__title")

    def get_options(self, obj):
        return ", ".join([option.text for option in obj.options.all()])

    get_options.short_description = "Options"
