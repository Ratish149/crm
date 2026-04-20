from django.urls import path

from .views import (
    DiscoveryQuestionListView,
    LeadDiscoveryAnswerListCreateView,
)

urlpatterns = [
    path(
        "discovery/questions/",
        DiscoveryQuestionListView.as_view(),
        name="discovery-questions",
    ),
    path(
        "discovery/answers/",
        LeadDiscoveryAnswerListCreateView.as_view(),
        name="discovery-answers",
    ),
]
