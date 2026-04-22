from django.urls import path

from .views import (
    AnswerDetailView,
    AnswerListCreateView,
    CategoryDetailView,
    CategoryListCreateView,
    DiscoveryConfigView,
    GenerateStageAnalysisView,
    LeadResponseDetailView,
    LeadResponseListCreateView,
    LeadStageAnalysisDetailView,
    QuestionDetailView,
    QuestionListCreateView,
    SalesStageDetailView,
    SalesStageListCreateView,
)

urlpatterns = [
    # Core Config
    path("discovery/stages/", SalesStageListCreateView.as_view(), name="stage-list"),
    path(
        "discovery/stages/<int:pk>/",
        SalesStageDetailView.as_view(),
        name="stage-detail",
    ),
    path(
        "discovery/categories/", CategoryListCreateView.as_view(), name="category-list"
    ),
    path(
        "discovery/categories/<int:pk>/",
        CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path(
        "discovery/questions/", QuestionListCreateView.as_view(), name="question-list"
    ),
    path(
        "discovery/questions/<int:pk>/",
        QuestionDetailView.as_view(),
        name="question-detail",
    ),
    path("discovery/answers/", AnswerListCreateView.as_view(), name="answer-list"),
    path(
        "discovery/answers/<int:pk>/", AnswerDetailView.as_view(), name="answer-detail"
    ),
    path("discovery/config/", DiscoveryConfigView.as_view(), name="discovery-config"),
    # Responses
    path(
        "discovery/responses/",
        LeadResponseListCreateView.as_view(),
        name="response-list",
    ),
    path(
        "discovery/responses/<int:pk>/",
        LeadResponseDetailView.as_view(),
        name="response-detail",
    ),
    # Analysis
    path(
        "discovery/analyze/",
        GenerateStageAnalysisView.as_view(),
        name="generate-analysis",
    ),
    path(
        "discovery/analysis/",
        LeadStageAnalysisDetailView.as_view(),
        name="analysis-detail",
    ),
]
