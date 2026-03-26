from django.urls import path
from . import views

urlpatterns =[
    path('generate-questionnaire/', views.generar_cuestionario, name='generar_cuestionario'),
    path('estado/<int:pk>/', views.consultar_estado_cuestionario, name='consultar_estado'),
]