import django_filters

from .models import ActivityTimeline, Followup, Lead


class LeadFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(method="filter_by_tags")
    preset = django_filters.NumberFilter(method="filter_by_preset")

    def filter_by_preset(self, queryset, name, value):
        if not value:
            return queryset
        try:
            from .models import FilterPreset

            preset_obj = FilterPreset.objects.get(id=value)
            filters_data = preset_obj.filters.copy() if preset_obj.filters else {}
            filters_data.pop("preset", None)  # Prevent infinite recursion

            # Temporarily pass the preset filters as data to a new instance of the same FilterSet
            fs = self.__class__(filters_data, queryset=queryset)
            return fs.qs
        except Exception:
            return queryset

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


class FollowupFilter(django_filters.FilterSet):
    month = django_filters.NumberFilter(field_name="followup_date", lookup_expr="month")
    year = django_filters.NumberFilter(field_name="followup_date", lookup_expr="year")
    day = django_filters.NumberFilter(field_name="followup_date", lookup_expr="day")
    start_date = django_filters.DateFilter(
        field_name="followup_date", lookup_expr="gte"
    )
    end_date = django_filters.DateFilter(field_name="followup_date", lookup_expr="lte")

    class Meta:
        model = Followup
        fields = ["status", "lead"]
