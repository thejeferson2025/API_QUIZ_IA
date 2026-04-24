from django.urls import path
from . import views

#endpoints para el cuestionario
urlpatterns =[
    path('process-questionnaire/', views.generar_cuestionario, name='generar_cuestionario'),
    path('generate-questionnaire/<int:pk>/', views.consultar_estado_cuestionario, name='consultar_estado'),
]