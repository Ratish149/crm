import json
import os

from django.shortcuts import get_object_or_404

# from dotenv import load_dotenv
from google import genai
from rest_framework import generics, response, status, views

from discovery.serializers import SalesStageDetailSerializer

from .models import (
    Answer,
    Category,
    Lead,
    LeadResponse,
    LeadStageAnalysis,
    Question,
    SalesStage,
)
from .serializers import (
    AnswerSerializer,
    CategorySerializer,
    LeadResponseCreateSerializer,
    LeadResponseReadSerializer,
    LeadStageAnalysisSerializer,
    QuestionSerializer,
    SalesStageSerializer,
)

# load_dotenv()


# New google-genai SDK


class SalesStageListCreateView(generics.ListCreateAPIView):
    queryset = SalesStage.objects.all()
    serializer_class = SalesStageSerializer


class SalesStageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SalesStage.objects.all()
    serializer_class = SalesStageSerializer


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class QuestionListCreateView(generics.ListCreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class AnswerListCreateView(generics.ListCreateAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


class AnswerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


class DiscoveryConfigView(views.APIView):
    """
    Returns all stages, each containing its nested questions and answers.
    """

    def get(self, request):
        # We use prefetch_related to load questions and their answers in
        # a single optimized database hit.
        stages = SalesStage.objects.prefetch_related(
            "questions__answers", "questions__category"
        ).all()

        serializer = SalesStageDetailSerializer(stages, many=True)
        return response.Response(serializer.data)


class LeadResponseListCreateView(generics.ListCreateAPIView):
    """
    Handle Lead responses for any stage.
    """

    def get_serializer_class(self):
        if self.request.method == "GET":
            return LeadResponseReadSerializer
        return LeadResponseCreateSerializer

    def get_queryset(self):
        queryset = LeadResponse.objects.all()
        lead_id = self.request.query_params.get("lead_id")
        stage_id = self.request.query_params.get("stage_id")

        if lead_id:
            queryset = queryset.filter(lead_id=lead_id)
        if stage_id:
            queryset = queryset.filter(question__stage_id=stage_id)

        return queryset


class LeadResponseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LeadResponse.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return LeadResponseCreateSerializer
        return LeadResponseReadSerializer


class GenerateStageAnalysisView(views.APIView):
    """
    Triggers Gemini AI to analyze the responses for a specific lead and stage.
    """

    def post(self, request):
        lead_id = request.data.get("lead_id")
        stage_id = request.data.get("stage_id")

        lead = get_object_or_404(Lead, id=lead_id)
        stage = get_object_or_404(SalesStage, id=stage_id)

        # 1. Gather all responses for this lead in this stage
        responses_qs = LeadResponse.objects.filter(lead=lead, question__stage=stage)

        if not responses_qs.exists():
            return response.Response(
                {"error": f"No responses found for {lead.full_name} in {stage.name}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Format the data for the AI
        response_data = []
        for r in responses_qs:
            answers = [a.text for a in r.selected_answers.all()]
            response_data.append({
                "question": r.question.text,
                "answers": answers,
                "text_response": r.text_value,
            })

        prompt = f"""
        Analyze these sales {stage.name} responses for {lead.full_name}:
        Data: {json.dumps(response_data)}
        
        Pitching: "Nepdora" (Nepali website builder).
        
        Return JSON exactly:
        {{
            "client_problems": "Short bullet points of the main pain points.",
            "recommended_approach": "One or two concise sentences on the best pitch strategy."
        }}
        
        Constraint: Keep descriptions extremely brief and professional.
        """

        # 3. Call Gemini (Removed the simulated fallback to force visibility of errors)
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            return response.Response(
                {"error": "GEMINI_API_KEY is not configured in environment variables."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # Initialize Client
            client = genai.Client(api_key=api_key)

            # Using 1.5-flash as it is fast and reliable for JSON tasks
            ai_resp = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview", contents=prompt
            )

            # Extract and Clean JSON
            resp_text = ai_resp.text
            if "```json" in resp_text:
                resp_text = resp_text.split("```json")[1].split("```")[0].strip()
            elif "```" in resp_text:
                resp_text = resp_text.split("```")[1].split("```")[0].strip()

            ai_data = json.loads(resp_text)

        except Exception as e:
            return response.Response(
                {"error": f"AI Generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 4. Save/Update Analysis
        analysis, created = LeadStageAnalysis.objects.update_or_create(
            lead=lead,
            stage=stage,
            defaults={
                "client_problems": ai_data.get(
                    "client_problems", "No problems identified."
                ),
                "recommended_approach": ai_data.get(
                    "recommended_approach", "No approach recommended."
                ),
                "raw_ai_response": ai_data,
            },
        )

        return response.Response(LeadStageAnalysisSerializer(analysis).data)


class LeadStageAnalysisDetailView(generics.RetrieveAPIView):
    """
    Retrieves the analysis for a specific lead and stage.
    """

    queryset = LeadStageAnalysis.objects.all()
    serializer_class = LeadStageAnalysisSerializer

    def get_object(self):
        lead_id = self.request.query_params.get("lead_id")
        stage_id = self.request.query_params.get("stage_id")
        return get_object_or_404(LeadStageAnalysis, lead_id=lead_id, stage_id=stage_id)
