from django.db import models

# Create your models here.


class KnowledgeCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class KnowledgeBase(models.Model):
    category = models.ForeignKey(
        KnowledgeCategory,
        on_delete=models.CASCADE,
        related_name="knowledge_bases",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
