import django_filters

from .models import KnowledgeBase


class KnowledgeBaseFilter(django_filters.FilterSet):
    class Meta:
        model = KnowledgeBase
        fields = ["category"]
