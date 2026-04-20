from django.urls import path

from .views import (
    LeadListCreateView,
    LeadPipelineView,
    LeadRetrieveUpdateDestroyView,
    NoteCreateView,
)

urlpatterns = [
    path("lead/", LeadListCreateView.as_view(), name="lead-list-create"),
    path("lead/<int:pk>/", LeadRetrieveUpdateDestroyView.as_view(), name="lead-detail"),
    path("notes/", NoteCreateView.as_view(), name="note-create"),
    path("lead-pipeline/", LeadPipelineView.as_view(), name="lead-pipeline"),
]
