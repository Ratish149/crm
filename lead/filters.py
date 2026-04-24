import django_filters

from .models import ActivityTimeline, Lead


class LeadFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(method="filter_by_tags")

    def filter_by_tags(self, queryset, name, value):
        if not value:
            return queryset
        tag_names = [t.strip() for t in value.split(",")]
        return queryset.filter(tags__name__in=tag_names).distinct()

    min_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")
    max_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="lte")

    class Meta:
        model = Lead
        fields = ["status", "source", "assigned_to", "rating"]


class ActivityTimelineFilter(django_filters.FilterSet):
    class Meta:
        model = ActivityTimeline
        fields = ["activity_type"]
