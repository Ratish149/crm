from rest_framework import serializers

from .models import (
    Answer,
    Category,
    LeadResponse,
    LeadStageAnalysis,
    Question,
    SalesStage,
)


class SalesStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesStage
        fields = ["id", "name", "order", "description"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class AnswerSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Answer
        fields = ["id", "text", "description", "question", "category", "category_name"]


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "stage",
            "text",
            "description",
            "question_type",
            "order",
            "answers",
            "category",
            "category_name",
        ]


class LeadResponseReadSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)
    selected_answers_detail = AnswerSerializer(
        source="selected_answers", many=True, read_only=True
    )
    stage_name = serializers.CharField(source="question.stage.name", read_only=True)

    class Meta:
        model = LeadResponse
        fields = [
            "id",
            "lead",
            "question",
            "question_text",
            "stage_name",
            "selected_answers",
            "selected_answers_detail",
            "text_value",
            "created_at",
        ]


class LeadResponseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadResponse
        fields = ["lead", "question", "selected_answers", "text_value"]


class LeadStageAnalysisSerializer(serializers.ModelSerializer):
    stage_name = serializers.CharField(source="stage.name", read_only=True)

    class Meta:
        model = LeadStageAnalysis
        fields = [
            "id",
            "lead",
            "stage",
            "stage_name",
            "client_problems",
            "recommended_approach",
            "raw_ai_response",
            "created_at",
        ]


class SalesStageDetailSerializer(serializers.ModelSerializer):
    # This matches the related_name="questions" in the Question model
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = SalesStage
        fields = ["id", "name", "order", "description", "questions"]
