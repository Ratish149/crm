from rest_framework import serializers

from .models import DiscoveryOption, DiscoveryQuestion, LeadDiscoveryAnswer


class DiscoveryOptionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = DiscoveryOption
        fields = ["id", "text", "category", "category_name"]


class DiscoveryQuestionSerializer(serializers.ModelSerializer):
    options = DiscoveryOptionSerializer(many=True, read_only=True)

    class Meta:
        model = DiscoveryQuestion
        fields = ["id", "title", "options"]


class LeadDiscoveryAnswerSerializer(serializers.ModelSerializer):
    options = serializers.PrimaryKeyRelatedField(
        queryset=DiscoveryOption.objects.all(), many=True
    )

    class Meta:
        model = LeadDiscoveryAnswer
        fields = "__all__"
        validators = []  # Bypass UniqueTogetherValidator to handle upsert in view


class LeadDiscoveryAnswerReadSerializer(serializers.ModelSerializer):
    question_title = serializers.CharField(source="question.title", read_only=True)
    options = DiscoveryOptionSerializer(many=True, read_only=True)

    class Meta:
        model = LeadDiscoveryAnswer
        fields = [
            "id",
            "lead",
            "question",
            "question_title",
            "options",
            "updated_at",
        ]
