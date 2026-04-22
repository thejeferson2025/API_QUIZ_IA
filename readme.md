# API Generador de Cuestionarios Interactivos con IA

Este proyecto es una API RESTful desarrollada con Django y Python que permite la generación automatizada de cuestionarios interactivos a partir de videos de clases magistrales. Utiliza un enfoque asíncrono (Celery + Redis) para procesar archivos multimedia pesados y se integra con la API de Google Gemini para el análisis de contenido.

## 🛠️ Requisitos Previos

Antes de clonar el proyecto, asegúrate de tener instalado en tu sistema:
- **Python:** 3.13.2
- **Docker Desktop** (Para levantar el servidor de Redis).
- **SQL Server** (Para la base de datos relacional).
- **FFmpeg:** Configurado en las variables de entorno de tu sistema operativo.

## ⚙️ Instalación y Configuración

**1. Clonar el repositorio y entrar al directorio:**  
```bash
git clone https://github.com/thejeferson2025/API_QUIZ_IA.git
cd API_QUIZ_IA
```
**2. Crear y activar un entorno virtual:**  
```bash
# En Windows:
python -m venv .venv
.venv\Scripts\activate
```

**3. Instalar las dependencias del proyecto:**  
```bash
pip install -r requirements.txt
```
**4. Configurar Variables de Entorno:**  
Crea un archivo llamado .env en la raíz del proyecto basándote en el archivo **.env.template** y añade tu clave de API de Gemini y las credenciales de tu SQL Server.

 - Levantando el Broker (Redis con Docker)
El sistema necesita Redis para gestionar la cola de tareas en segundo plano. Si ya tienes Docker Desktop abierto, ejecuta el siguiente comando para descargar y correr un contenedor de Redis en el puerto por defecto (6379):
```bash
docker run --name redis_broker -p 6379:6379 -d redis
```
***(Nota: Si detienes el contenedor, puedes volver a iniciarlo desde la interfaz de Docker Desktop o con el comando docker start redis_broker).***
- Base de Datos y Migraciones
Una vez que tengas tu SQL Server corriendo y configurado en el proyecto, prepara la base de datos ejecutando las migraciones:
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🚀 Ejecución del Proyecto
Para que el sistema funcione correctamente, necesitas ejecutar el servidor web y el worker asíncrono en dos terminales separadas (ambas con el entorno virtual activado):

Terminal 1 (Servidor de Django):
```bash
python manage.py runserver
```
Terminal 2 (Celery Worker):
```bash
celery -A gemini_api worker -l INFO --pool=solo
```
## 📄 Documentación de la API
Una vez que el proyecto esté corriendo, puedes acceder a la interfaz interactiva de la API (Swagger) visitando:  
http://127.0.0.1:8000/swagger/