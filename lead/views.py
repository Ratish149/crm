from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, views
from rest_framework.response import Response

from crm.utils import CustomPagination

from .filters import ActivityTimelineFilter, LeadFilter
from .models import ActivityTimeline, Lead, LeadDocument, Note
from .serializers import (
    ActivityTimelineSerializer,
    LeadDetailSerializer,
    LeadDocumentSerializer,
    LeadListSerializer,
    LeadPipelineSerializer,
    LeadSerializer,
    NoteSerializer,
)
from .utils import log_activity


class LeadListCreateView(generics.ListCreateAPIView):
    queryset = Lead.objects.all().order_by("-created_at")
    serializer_class = LeadSerializer
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = LeadFilter
    search_fields = ["full_name", "phone_number"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return LeadListSerializer
        return LeadSerializer

    def perform_create(self, serializer):
        lead = serializer.save(created_by=self.request.user)
        log_activity(
            lead=lead,
            activity_type="lead_created",
            user=self.request.user,
            description={"message": f"Lead '{lead.full_name}' was created."},
        )


class LeadRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return LeadDetailSerializer
        return LeadSerializer


class NoteCreateView(generics.CreateAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        note = serializer.save(created_by=self.request.user)
        log_activity(
            lead=note.lead,
            activity_type="note_added",
            user=self.request.user,
            description={
                "message": "A new note was added.",
                "note_content": note.content,
                "note_id": note.id,
            },
        )


class LeadPipelineView(views.APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Lead.objects.all().select_related("assigned_to")

        # Apply filters
        filterset = LeadFilter(request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs

        pipeline = {}
        for status, label in Lead.STATUS_CHOICES:
            leads = queryset.filter(status=status)
            pipeline[status] = LeadPipelineSerializer(leads, many=True).data

        return Response(pipeline)


class LeadActivityTimelineView(generics.ListAPIView):
    serializer_class = ActivityTimelineSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ActivityTimelineFilter

    def get_queryset(self):
        lead_id = self.kwargs.get("lead_id")
        return ActivityTimeline.objects.filter(lead_id=lead_id).order_by("-created_at")


class LeadDocumentCreateView(generics.CreateAPIView):
    queryset = LeadDocument.objects.all()
    serializer_class = LeadDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        document = serializer.save(uploaded_by=self.request.user)
        log_activity(
            lead=document.lead,
            activity_type="document_uploaded",
            user=self.request.user,
            description={
                "message": f"A new document '{document.file.name}' was uploaded.",
                "document_id": document.id,
            },
        )


class LeadDocumentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LeadDocument.objects.all()
    serializer_class = LeadDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]


class LeadDocumentListView(generics.ListAPIView):
    serializer_class = LeadDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        lead_id = self.kwargs.get("lead_id")
        return LeadDocument.objects.filter(lead_id=lead_id).order_by("-uploaded_at")
