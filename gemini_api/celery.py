import os
from celery import Celery

# Establece el módulo de configuración de Django por defecto para celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gemini_api.settings')

app = Celery('gemini_api')

# Lee la configuración de Django buscando variables que empiecen con 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubre automáticamente las tareas en todos los archivos 'tasks.py' de la app
app.autodiscover_tasks()