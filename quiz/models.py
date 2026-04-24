from django.db import models

class Carrera(models.Model):
    nombre = models.CharField(max_length=255)
    
    def __str__(self):
        return self.nombre

class Asignatura(models.Model):
    nombre = models.CharField(max_length=255)
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='asignaturas')
    
    def __str__(self):
        return f"{self.nombre} - {self.carrera.nombre}"

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
    asignatura = models.ForeignKey(Asignatura, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    
    def __str__(self):
        return f"{self.video_name} - {self.status}"