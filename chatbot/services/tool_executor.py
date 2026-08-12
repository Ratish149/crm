from django.db.models import Count, Q

from lead.models import Lead, Followup, ActivityTimeline
from knowledgebase.models import KnowledgeBase


def execute_tool(user, name, args):
    if name == "get_conversion_pipeline":
        qs = Lead.objects.all()
        if args.get("start_date"):
            qs = qs.filter(created_at__gte=args["start_date"])
        if args.get("end_date"):
            qs = qs.filter(created_at__lte=args["end_date"])

        total = qs.count()
        counts = dict(qs.values_list("status").annotate(count=Count("id")))

        funnel = ["new", "discovery", "quoted", "negotiation", "closed"]
        pipeline = []
        for i, stage in enumerate(funnel):
            count = counts.get(stage, 0)
            prev_stage = funnel[i - 1] if i > 0 else None
            prev_count = counts.get(prev_stage, 0) if prev_stage else total
            pipeline.append(
                {
                    "stage": stage,
                    "count": count,
                    "percent_of_total": round(count / total * 100, 1) if total else 0.0,
                    "conversion_from_previous": round(count / prev_count * 100, 1) if prev_count else 0.0,
                    "conversion_from_new": round(count / counts.get("new", 0) * 100, 1) if counts.get("new", 0) else 0.0,
                }
            )

        return {
            "total_leads": total,
            "pipeline": pipeline,
            "not_interested": counts.get("not_interested", 0),
        }

    elif name == "get_lead_stats":
        qs = Lead.objects.all()
        if args.get("start_date"):
            qs = qs.filter(created_at__gte=args["start_date"])
        if args.get("end_date"):
            qs = qs.filter(created_at__lte=args["end_date"])
        status = args.get("status")
        if status and status != "all":
            qs = qs.filter(status=status)

        return list(qs.values("status", "source").annotate(count=Count("id")))

    elif name == "search_leads":
        qs = Lead.objects.all()
        query = args.get("query")
        if query:
            qs = qs.filter(Q(full_name__icontains=query) | Q(email__icontains=query))
        if args.get("status"):
            qs = qs.filter(status=args["status"])
        return list(
            qs.values("id", "full_name", "email", "status", "estimate_value", "assigned_to__username")[:20]
        )

    elif name == "get_lead_detail":
        qs = Lead.objects.all()
        if args.get("lead_id"):
            lead = qs.filter(id=args["lead_id"]).first()
        elif args.get("full_name"):
            lead = qs.filter(full_name__iexact=args["full_name"]).first()
        else:
            return {"error": "lead_id or full_name required"}

        if not lead:
            return {"error": "lead not found"}

        recent_activity = list(
            ActivityTimeline.objects.filter(lead=lead)
            .order_by("-created_at")[:5]
            .values("activity_type", "description", "created_at")
        )

        return {
            "id": lead.id,
            "full_name": lead.full_name,
            "email": lead.email,
            "phone_number": lead.phone_number,
            "status": lead.status,
            "source": lead.source,
            "estimate_value": lead.estimate_value,
            "rating": lead.rating,
            "assigned_to": lead.assigned_to.username if lead.assigned_to else None,
            "recent_activity": recent_activity,
        }

    elif name == "get_upcoming_followups":
        qs = Followup.objects.filter(status="pending")
        if args.get("lead_id"):
            qs = qs.filter(lead_id=args["lead_id"])
        if args.get("only_mine"):
            qs = qs.filter(created_by=user)
        return list(
            qs.order_by("followup_date").values(
                "id", "lead__full_name", "followup_date", "followup_time", "notes"
            )[:20]
        )

    elif name == "search_knowledge_base":
        query = args["query"]
        qs = KnowledgeBase.objects.filter(Q(title__icontains=query) | Q(content__icontains=query))
        return list(qs.values("id", "title", "content")[:5])

    elif name == "get_recent_leads":
        qs = Lead.objects.all().order_by("-created_at")
        if args.get("status"):
            qs = qs.filter(status=args["status"])
        limit = min(args.get("limit") or 5,50)
        return list(
            qs.values("id", "full_name", "email", "status", "estimate_value", "created_at")[:limit]
        )

    raise ValueError(f"Unknown tool: {name}")