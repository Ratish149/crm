from django.db import models

# Create your models here.
class Notification(models.Model):
    title=models.CharField(max_length=50)
    description=models.CharField(max_length=255)

    


