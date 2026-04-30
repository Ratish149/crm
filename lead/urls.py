from django.urls import path

from .views import (
    AllFollowupListView,
    CheckUpcomingFollowupsView,
    FilterPresetListCreateView,
    FilterPresetRetrieveUpdateDestroyView,
    FollowupListCreateView,
    FollowupRetrieveUpdateDestroyView,
    IncompleteFollowupListView,
    LeadActivityTimelineView,
    LeadBulkImportView,
    LeadDocumentCreateView,
    LeadDocumentListView,
    LeadDocumentRetrieveUpdateDestroyView,
    LeadImportTemplateView,
    LeadListCreateView,
    LeadPipelineView,
    LeadRetrieveUpdateDestroyView,
    NoteCreateView,
    TagListView,
)

urlpatterns = [
    path("followups/", AllFollowupListView.as_view(), name="followup-list"),
    path(
        "followups/incomplete/",
        IncompleteFollowupListView.as_view(),
        name="incomplete-followup-list",
    ),
    path("lead/", LeadListCreateView.as_view(), name="lead-list-create"),
    path("lead/<int:pk>/", LeadRetrieveUpdateDestroyView.as_view(), name="lead-detail"),
    path(
        "lead/<int:lead_id>/activities/",
        LeadActivityTimelineView.as_view(),
        name="lead-activities",
    ),
    path("notes/", NoteCreateView.as_view(), name="note-create"),
    path("lead-pipeline/", LeadPipelineView.as_view(), name="lead-pipeline"),
    path("documents/", LeadDocumentCreateView.as_view(), name="document-create"),
    path(
        "documents/<int:pk>/",
        LeadDocumentRetrieveUpdateDestroyView.as_view(),
        name="document-detail",
    ),
    path(
        "lead/<int:lead_id>/documents/",
        LeadDocumentListView.as_view(),
        name="lead-documents",
    ),
    path(
        "lead/<int:lead_id>/followups/",
        FollowupListCreateView.as_view(),
        name="lead-followups",
    ),
    path(
        "followups/<int:pk>/",
        FollowupRetrieveUpdateDestroyView.as_view(),
        name="followup-detail",
    ),
    path(
        "check-followups/",
        CheckUpcomingFollowupsView.as_view(),
        name="check-upcoming-followups",
    ),
    path("tags/", TagListView.as_view(), name="tag-list"),
    path(
        "lead/import-template/",
        LeadImportTemplateView.as_view(),
        name="lead-import-template",
    ),
    path("lead/bulk-import/", LeadBulkImportView.as_view(), name="lead-bulk-import"),
    path(
        "filter-presets/",
        FilterPresetListCreateView.as_view(),
        name="filter-preset-list",
    ),
    path(
        "filter-presets/<int:pk>/",
        FilterPresetRetrieveUpdateDestroyView.as_view(),
        name="filter-preset-detail",
    ),
]
