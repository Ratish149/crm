from django.urls import path

from .views import SendExclusiveOfferEmailView, SendLeadEmailView

urlpatterns = [
    path("lead/send-email/", SendLeadEmailView.as_view(), name="lead-send-email"),
    path(
        "lead/send-proposal/",
        SendExclusiveOfferEmailView.as_view(),
        name="lead-send-proposal",
    ),
]
