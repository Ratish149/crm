from django.db import models

from lead.models import Lead


class SalesStage(models.Model):
    """
    Represents the stages of the sales process (e.g., Discovery, Qualify, Close).
    """

    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(
        default=0, help_text="Order in which the stage appears"
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Groups questions and answers by topic (e.g., 'Online Presence', 'Pain Signals').
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Question(models.Model):
    """
    A specific question within a sales stage.
    """

    QUESTION_TYPES = [
        ("checklist", "Checklist (Multiple Selection)"),
        ("single", "Single Choice"),
        ("text", "Free Text"),
    ]

    stage = models.ForeignKey(
        SalesStage, on_delete=models.CASCADE, related_name="questions"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    text = models.TextField(help_text="The main question text")
    description = models.TextField(
        blank=True, help_text="Subtext or instructions for the salesperson"
    )
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPES, default="checklist"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.stage.name} - {self.text[:50]}"


class Answer(models.Model):
    """
    Expected selections or responses for a question.
    """

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="answers",
    )
    text = models.TextField(help_text="The text for the checkbox or option")
    description = models.TextField(
        blank=True, help_text="Additional context for this specific option"
    )

    def __str__(self):
        return self.text


class LeadResponse(models.Model):
    """
    Stores a lead's answers to specific questions in any stage.
    """

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer, blank=True)
    text_value = models.TextField(
        blank=True, null=True, help_text="For free-text question types"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.full_name} - {self.question.text[:30]}"


class LeadStageAnalysis(models.Model):
    """
    Stores AI-generated analysis (Gemini API) for each stage of a specific lead.
    """

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="analyses")
    stage = models.ForeignKey(SalesStage, on_delete=models.CASCADE)
    client_problems = models.TextField(help_text="Identified problems or pain points")
    recommended_approach = models.TextField(
        help_text="Suggested strategy to pitch Nepdora"
    )
    raw_ai_response = models.JSONField(
        null=True, blank=True, help_text="Full JSON response from Gemini"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("lead", "stage")
        verbose_name_plural = "Lead Stage Analyses"

    def __str__(self):
        return f"{self.lead.full_name} - {self.stage.name} Analysis"
