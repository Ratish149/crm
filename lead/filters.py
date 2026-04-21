import django_filters

from .models import ActivityTimeline, Lead


class LeadFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(field_name="tags__name", lookup_expr="icontains")
    min_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")
    max_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="lte")

    class Meta:
        model = Lead
        fields = ["status", "source", "assigned_to", "rating"]


class ActivityTimelineFilter(django_filters.FilterSet):
    class Meta:
        model = ActivityTimeline
        fields = ["activity_type"]
