from rest_framework import generics, permissions

from lead.utils import log_activity

from .models import DiscoveryQuestion, LeadDiscoveryAnswer
from .serializers import (
    DiscoveryQuestionSerializer,
    LeadDiscoveryAnswerReadSerializer,
    LeadDiscoveryAnswerSerializer,
)


class DiscoveryQuestionListView(generics.ListAPIView):
    queryset = DiscoveryQuestion.objects.all()
    serializer_class = DiscoveryQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]


class LeadDiscoveryAnswerListCreateView(generics.ListCreateAPIView):
    queryset = LeadDiscoveryAnswer.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LeadDiscoveryAnswerSerializer
        return LeadDiscoveryAnswerReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        lead_id = self.request.query_params.get("lead")
        if lead_id:
            queryset = queryset.filter(lead_id=lead_id)
        return queryset

    def perform_create(self, serializer):
        # Handle upsert: update if (lead, question) exists, else create
        lead = serializer.validated_data.get("lead")
        question = serializer.validated_data.get("question")
        options = serializer.validated_data.get("options")

        answer, created = LeadDiscoveryAnswer.objects.update_or_create(
            lead=lead, question=question, defaults={}
        )
        answer.options.set(options)

        log_activity(
            lead=answer.lead,
            activity_type="discovery_updated",
            user=self.request.user,
            description={
                "message": f"Lead updated discovery question: {question.title}",
                "selected_options": [o.text for o in options],
            },
        )
