
### Version de Python necesaria para el proyecto
- 3.13.2

### Comando para iniciar el proyecto
 ABRIR 2 TERMINALES 
 - EN EL PRIMER TERMINAL: 
    - python manage.py runserver
 - EN EL SEGUNDO TERMINAL: 
    - celery -A gemini_api worker -l INFO --pool=solo


### Tener levanto el docker (run) e iniciar el servicio de redis