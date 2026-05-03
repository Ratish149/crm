import csv
import io
from datetime import timedelta

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from crm.utils import CustomPagination, send_resend_email

from .filters import ActivityTimelineFilter, FollowupFilter, LeadFilter
from .models import (
    ActivityTimeline,
    FilterPreset,
    Followup,
    Lead,
    LeadDocument,
    Note,
    Tag,
)
from .serializers import (
    ActivityTimelineSerializer,
    FilterPresetSerializer,
    FollowupListReadSerializer,
    FollowupSerializer,
    LeadDetailSerializer,
    LeadDocumentSerializer,
    LeadListSerializer,
    LeadPipelineSerializer,
    LeadSerializer,
    NoteSerializer,
    TagSerializer,
)
from .tasks import check_and_notify_upcoming_followups
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


class LeadPipelineView(generics.GenericAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = LeadFilter
    search_fields = ["full_name", "phone_number"]

    def get(self, request, *args, **kwargs):
        queryset = (
            Lead.objects.all().select_related("assigned_to").order_by("-created_at")
        )

        queryset = self.filter_queryset(queryset)

        pipeline = {}
        for s_code, label in Lead.STATUS_CHOICES:
            leads = queryset.filter(status=s_code)

            # Instantiate the pagination class defined on the view
            paginator = self.pagination_class()

            # Give each column its own pagination parameter (e.g., ?page_new=2, ?page_contacted=3)
            paginator.page_query_param = f"page_{s_code}"

            paginated_leads = paginator.paginate_queryset(leads, request, view=self)

            pipeline[s_code] = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": LeadPipelineSerializer(paginated_leads, many=True).data,
            }

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


class FollowupListCreateView(generics.ListCreateAPIView):
    serializer_class = FollowupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        lead_id = self.kwargs.get("lead_id")
        return Followup.objects.filter(lead_id=lead_id).order_by(
            "followup_date", "followup_time"
        )

    def perform_create(self, serializer):
        followup = serializer.save(created_by=self.request.user)

        from django.utils import timezone

        today = timezone.localdate()
        if followup.followup_date and followup.followup_date <= today + timedelta(
            days=1
        ):
            self.send_followup_notification(followup)

    def send_followup_notification(self, followup):
        lead = followup.lead
        assigned_user = lead.assigned_to

        if assigned_user and assigned_user.email:
            subject = f"Upcoming Follow-up: {lead.full_name}"
            html_content = f"""
                <h3>Follow-up Reminder</h3>
                <p>You have an upcoming follow-up with <strong>{lead.full_name}</strong>.</p>
                <p><strong>Date:</strong> {followup.followup_date}</p>
                <p><strong>Time:</strong> {followup.followup_time or "Not specified"}</p>
                <p><strong>Notes:</strong> {followup.notes or "No notes provided"}</p>
                <p>View lead details: <a href="http://localhost:3000/leads/{lead.id}">Click here</a></p>
            """
            send_resend_email(assigned_user.email, subject, html_content)


class FollowupRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Followup.objects.all()
    serializer_class = FollowupSerializer
    permission_classes = [permissions.IsAuthenticated]


class AllFollowupListView(generics.ListAPIView):
    queryset = Followup.objects.all()
    serializer_class = FollowupListReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = FollowupFilter
    search_fields = ["lead__full_name", "notes"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        # If no specific date filters are provided, default to current week
        date_filters = ["month", "day", "year", "start_date", "end_date"]
        if not any(param in params for param in date_filters):
            from datetime import timedelta

            from django.utils import timezone

            today = timezone.localdate()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            queryset = queryset.filter(
                followup_date__range=[start_of_week, end_of_week]
            )

        # If month or day is provided but year is not, default to current year
        elif ("month" in params or "day" in params) and "year" not in params:
            from django.utils import timezone

            queryset = queryset.filter(followup_date__year=timezone.localdate().year)

        return queryset.order_by("followup_date", "followup_time")


class IncompleteFollowupListView(generics.ListAPIView):
    queryset = Followup.objects.exclude(status="completed").order_by(
        "followup_date", "followup_time"
    )
    serializer_class = FollowupListReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = FollowupFilter
    search_fields = ["lead__full_name", "notes"]


class CheckUpcomingFollowupsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        notifications_sent = check_and_notify_upcoming_followups()
        return Response({
            "message": f"Checked for upcoming followups. Notifications sent: {notifications_sent}"
        })


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class LeadImportTemplateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="lead_import_template.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            "full_name",
            "email",
            "phone_number",
            "source",
            "estimate_value",
        ])
        # Add a sample row
        writer.writerow([
            "John Doe",
            "john@example.com",
            "9876543210",
            "Facebook",
            "1000",
        ])

        return response


class LeadBulkImportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.endswith(".csv"):
            return Response(
                {"error": "Only CSV files are supported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            decoded_file = file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
        except Exception as e:
            return Response(
                {"error": f"Failed to parse CSV: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success_count = 0
        errors = []

        for row_idx, row in enumerate(reader, start=2):
            # Clean row keys (strip whitespace)
            clean_row = {k.strip(): v.strip() if v else v for k, v in row.items()}

            # Basic validation
            if not clean_row.get("full_name") or not clean_row.get("phone_number"):
                errors.append({
                    "row": row_idx,
                    "error": "full_name and phone_number are required",
                })
                continue

            # Check if lead already exists
            if Lead.objects.filter(full_name=clean_row["full_name"]).exists():
                errors.append({
                    "row": row_idx,
                    "error": f"Lead with name '{clean_row['full_name']}' already exists",
                })
                continue

            if (
                clean_row.get("email")
                and Lead.objects.filter(email=clean_row["email"]).exists()
            ):
                errors.append({
                    "row": row_idx,
                    "error": f"Lead with email '{clean_row['email']}' already exists",
                })
                continue

            if Lead.objects.filter(phone_number=clean_row["phone_number"]).exists():
                errors.append({
                    "row": row_idx,
                    "error": f"Lead with phone number '{clean_row['phone_number']}' already exists",
                })
                continue

            # Force status to 'new' for all imported leads
            clean_row["status"] = "new"

            # Ensure rating is not overwritten if accidentally included
            clean_row.pop("rating", None)

            serializer = LeadSerializer(data=clean_row)
            if serializer.is_valid():
                lead = serializer.save(created_by=request.user)
                log_activity(
                    lead=lead,
                    activity_type="lead_created",
                    user=request.user,
                    description={"message": f"Lead '{lead.full_name}' was imported."},
                )
                success_count += 1
            else:
                errors.append({"row": row_idx, "error": serializer.errors})

        return Response(
            {
                "message": f"Import completed. {success_count} leads created.",
                "success_count": success_count,
                "errors": errors,
            },
            status=status.HTTP_201_CREATED
            if success_count > 0
            else status.HTTP_400_BAD_REQUEST,
        )


class FilterPresetListCreateView(generics.ListCreateAPIView):
    serializer_class = FilterPresetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FilterPreset.objects.all()


class FilterPresetRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FilterPresetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FilterPreset.objects.all()
