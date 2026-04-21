from rest_framework import serializers

from .models import KnowledgeBase, KnowledgeCategory


class KnowledgeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeCategory
        fields = "__all__"


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source="category.name")

    class Meta:
        model = KnowledgeBase
        fields = "__all__"
