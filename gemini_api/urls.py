from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración visual de tu página de Swagger
schema_view = get_schema_view(
   openapi.Info(
      title="IA Quiz API",
      default_version='v1',
      description="API educativa para generar cuestionarios a partir de videos.",
      contact=openapi.Contact(email="tu@email.com"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns =[
    path('admin/', admin.site.urls),
    path('api/', include('quiz.urls')), # Tu API real
    
    # --- Rutas para la documentación interactiva ---
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]