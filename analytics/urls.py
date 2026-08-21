from django.urls import path
from .views import AnalyticsView
urlpatterns=[
    path("stats/", AnalyticsView.as_view(), name="dashboard-stats")
]