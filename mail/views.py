import os

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import permissions, status, views
from rest_framework.response import Response

from crm.utils import send_resend_email
from lead.models import Lead
from lead.utils import log_activity


class SendLeadEmailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        lead_id = request.data.get("lead_id")
        subject = request.data.get("subject")
        body = request.data.get("body")

        if not all([lead_id, subject, body]):
            return Response(
                {"error": "lead_id, subject, and body are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return Response(
                {"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not lead.email:
            return Response(
                {"error": "Lead does not have an email address"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send the email using the utility function
        email_sent = send_resend_email(lead.email, subject, body)

        if email_sent:
            # Log activity in the timeline
            log_activity(
                lead=lead,
                activity_type="email_sent",
                user=request.user,
                description={
                    "message": f"Email sent to {lead.email}",
                    "subject": subject,
                    "body": body,
                },
            )
            return Response(
                {"message": "Email sent successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "error": "Failed to send email. Please check your email configuration."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SendExclusiveOfferEmailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        name = request.data.get("name")
        email_address = request.data.get("email")
        website = request.data.get("website", "your website")
        date = request.data.get("date", "")
        paid_until = request.data.get("paid_until", "your trial ends")
        company_name = request.data.get("company_name", "")

        if not name or not email_address:
            return Response(
                {"error": "name and email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Try to find a lead to log activity
        lead = Lead.objects.filter(email=email_address).first()
        if not lead and company_name:
            lead = Lead.objects.filter(full_name__icontains=company_name).first()

        if not company_name:
            company_name = lead.full_name if lead else name

        if not date:
            if lead:
                date = lead.created_at.strftime("%B %d, %Y")
            else:
                date = timezone.now().strftime("%B %d, %Y")

        subject = f"Exclusive offer to get {company_name} online with Nepdora!"

        # Render HTML content from template
        context = {
            "name": name,
            "website": website,
            "date": date,
            "paid_until": paid_until,
            "company_name": company_name,
        }
        html_content = render_to_string("mail/exclusive_offer.html", context)

        # Prepare attachment
        attachments = []
        # Look in collected static first (production), then in assets (source/development)
        pdf_path = os.path.join(
            settings.STATIC_ROOT,
            "mail_template",
            "Website Development Proposal Nepdora.pdf",
        )
        if not os.path.exists(pdf_path):
            pdf_path = os.path.join(
                settings.BASE_DIR,
                "assets",
                "mail_template",
                "Website Development Proposal Nepdora.pdf",
            )

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                content = list(f.read())
                attachments.append({
                    "filename": "Website Development Proposal Nepdora.pdf",
                    "content": content,
                })

        email_sent = send_resend_email(
            email_address, subject, html_content, attachments=attachments
        )

        if email_sent:
            if lead:
                log_activity(
                    lead=lead,
                    activity_type="email_sent",
                    user=request.user,
                    description={
                        "message": f"Exclusive offer email sent to {email_address}",
                        "subject": subject,
                    },
                )
            return Response(
                {"message": "Exclusive offer email sent successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Failed to send email"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SendBusinessRecommendationEmailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        name = request.data.get("name")
        email_address = request.data.get("email")
        company_name = request.data.get("company_name", "")
        custom_content = request.data.get("custom_content", "")

        if not name or not email_address:
            return Response(
                {"error": "name and email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Try to find a lead to log activity
        lead = Lead.objects.filter(email=email_address).first()
        if not lead and company_name:
            lead = Lead.objects.filter(full_name__icontains=company_name).first()

        if not company_name:
            company_name = lead.full_name if lead else name

        subject = f"Growing {company_name} with Nepdora"

        # Render HTML content from template
        context = {
            "name": name,
            "company_name": company_name,
            "custom_content": custom_content,
        }
        html_content = render_to_string("mail/business_recommendation.html", context)

        # Prepare attachment
        attachments = []
        # Use the same PDF for now as per instructions or adjust if a specific one exists
        pdf_path = os.path.join(
            settings.STATIC_ROOT,
            "mail_template",
            "Website Development Proposal Nepdora.pdf",
        )
        if not os.path.exists(pdf_path):
            pdf_path = os.path.join(
                settings.BASE_DIR,
                "assets",
                "mail_template",
                "Website Development Proposal Nepdora.pdf",
            )

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                content = list(f.read())
                attachments.append({
                    "filename": "Website Development Proposal Nepdora.pdf",
                    "content": content,
                })

        email_sent = send_resend_email(
            email_address, subject, html_content, attachments=attachments
        )

        if email_sent:
            if lead:
                log_activity(
                    lead=lead,
                    activity_type="email_sent",
                    user=request.user,
                    description={
                        "message": f"Business recommendation email sent to {email_address}",
                        "subject": subject,
                    },
                )
            return Response(
                {"message": "Recommendation email sent successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Failed to send email"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
