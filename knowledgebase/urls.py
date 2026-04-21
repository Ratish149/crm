from django.urls import path

from .views import (
    KnowledgeBaseListCreateView,
    KnowledgeBaseRetrieveUpdateDestroyView,
    KnowledgeCategoryListCreateView,
    KnowledgeCategoryRetrieveUpdateDestroyView,
)

urlpatterns = [
    path(
        "categories/", KnowledgeCategoryListCreateView.as_view(), name="category-list-create"
    ),
    path(
        "categories/<int:pk>/",
        KnowledgeCategoryRetrieveUpdateDestroyView.as_view(),
        name="category-detail",
    ),
    path(
        "articles/", KnowledgeBaseListCreateView.as_view(), name="knowledgebase-list-create"
    ),
    path(
        "articles/<int:pk>/",
        KnowledgeBaseRetrieveUpdateDestroyView.as_view(),
        name="knowledgebase-detail",
    ),
]
