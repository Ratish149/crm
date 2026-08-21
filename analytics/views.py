from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from lead.models import Followup, Lead, LeadDocument, Note

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        week_ago = timezone.now() - timedelta(days=7)

        leads = Lead.objects.all()
        total_leads = leads.count()
        status_counts = dict(leads.values_list("status").annotate(count=Count("id")))

        lead_stats = leads.aggregate(
            new_this_week=Count("id", filter=Q(created_at__gte=week_ago)),
            new_this_month=Count(
                "id",
                filter=Q(created_at__year=today.year, created_at__month=today.month),
            ),
            unassigned=Count("id", filter=Q(assigned_to__isnull=True)),
            avg_rating=Avg("rating"),
        )

        followup_stats = Followup.objects.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            completed=Count("id", filter=Q(status="completed")),
            cancelled=Count("id", filter=Q(status="cancelled")),
            overdue=Count("id", filter=Q(status="pending", followup_date__lt=today)),
            due_today=Count("id", filter=Q(status="pending", followup_date=today)),
            upcoming=Count("id", filter=Q(status="pending", followup_date__gt=today)),
        )

        avg_rating = lead_stats["avg_rating"]
        return Response(
            {
                "total_leads": total_leads,
                "leads_by_status": status_counts,
                "new_leads_this_week": lead_stats["new_this_week"],
                "new_leads_this_month": lead_stats["new_this_month"],
                "unassigned_leads": lead_stats["unassigned"],
                "average_rating": round(avg_rating, 1) if avg_rating is not None else 0.0,
                "closed_rate": round(status_counts.get("closed", 0) / total_leads * 100, 1)
                if total_leads
                else 0.0,
                "followups": followup_stats,
                "total_notes": Note.objects.count(),
                "total_documents": LeadDocument.objects.count(),
            }
        )
