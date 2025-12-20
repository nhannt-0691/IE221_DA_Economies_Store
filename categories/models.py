from django.db import models
from django.utils import timezone



class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
