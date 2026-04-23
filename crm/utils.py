import resend
from django.conf import settings
from rest_framework.pagination import PageNumberPagination

resend.api_key = getattr(settings, "RESEND_API_KEY", None)


class CustomPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 100


def send_resend_email(to_email, subject, html_content):
    if not resend.api_key:
        print("Resend API key not configured.")
        return None

    params = {
        "from": "Baliyo CRM <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }

    try:
        email = resend.Emails.send(params)
        return email
    except Exception as e:
        print(f"Error sending email: {e}")
        return None
