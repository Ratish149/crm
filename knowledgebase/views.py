from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .filters import KnowledgeBaseFilter
from .models import KnowledgeBase, KnowledgeCategory
from .serializers import KnowledgeBaseSerializer, KnowledgeCategorySerializer


class KnowledgeCategoryListCreateView(generics.ListCreateAPIView):
    queryset = KnowledgeCategory.objects.all()
    serializer_class = KnowledgeCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class KnowledgeCategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = KnowledgeCategory.objects.all()
    serializer_class = KnowledgeCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class KnowledgeBaseListCreateView(generics.ListCreateAPIView):
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = KnowledgeBaseFilter
    search_fields = ["title", "content"]


class KnowledgeBaseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated]
