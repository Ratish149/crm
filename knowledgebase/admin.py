from django.contrib import admin
from django.db import models
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from .models import KnowledgeBase, KnowledgeCategory

# Register your models here.


@admin.register(KnowledgeCategory)
class KnowledgeCategoryAdmin(ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(ModelAdmin):
    list_display = ["title", "category"]
    list_filter = ["category"]
    search_fields = ["title", "category__name"]
    formfield_overrides = {
        models.TextField: {"widget": TinyMCE()},
    }
