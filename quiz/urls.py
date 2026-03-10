from django.urls import path
from . import views

urlpatterns =[
    path('generate-questionnaire/', views.generar_cuestionario, name='generar_cuestionario'),
]