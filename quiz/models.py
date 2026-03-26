from django.db import models

class VideoQuiz(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'Procesando'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]
    
    video_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    quiz_data = models.JSONField(null=True, blank=True) 
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.video_name} - {self.status}"