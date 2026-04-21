from django.urls import path

from .views import (
    LeadActivityTimelineView,
    LeadDocumentCreateView,
    LeadDocumentListView,
    LeadDocumentRetrieveUpdateDestroyView,
    LeadListCreateView,
    LeadPipelineView,
    LeadRetrieveUpdateDestroyView,
    NoteCreateView,
)

urlpatterns = [
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
]
