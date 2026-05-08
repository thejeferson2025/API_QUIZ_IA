# API Generador de Cuestionarios Interactivos con IA 🤖📹

Este proyecto es una API RESTful desarrollada con Django y Python que permite la generación automatizada de cuestionarios interactivos a partir de videos de clases magistrales.

Utiliza una arquitectura orquestada mediante Contenedores (Docker) e implementa un enfoque asíncrono (Celery + Redis) para el procesamiento de archivos multimedia pesados, integrándose con la API de Google Gemini para el análisis profundo de contenido educativo.

## 🛠️ Requisitos Previos

Gracias a la orquestación con Docker Compose, no necesitas instalar Python ni FFmpeg localmente, el entorno está completamente encapsulado.  
Solo asegúrate de tener en tu sistema:

- **Docker Desktop** (Obligatorio, con el motor en ejecución).
- **SQL Server** (Instalado localmente, con el modo de autenticación mixta/SQL Server habilitado,  tener una base de datos, un usuario y una contraseña activos).
- **Git** (Para clonar el repositorio).

## ⚙️ Instalación y Configuración

**1. Clonar el repositorio, entrar al directorio y abrirlo en VS Code:**  

```bash
git clone https://github.com/thejeferson2025/API_QUIZ_IA.git
cd API_QUIZ_IA
code .
```

**2. Configurar las Variables de Entorno:**  
Crea un archivo llamado `.env` en la raíz del proyecto basándote en el archivo `.env.template`. Solo necesitas modificar 4 datos clave:
- `GEMINI_API_KEY`: Tu clave de acceso de Google AI Studio.
- `DB_NAME`: El nombre de tu base de datos SQL Server.
- `DB_USER`: El usuario de tu base de datos SQL Server activo.
- `DB_PASSWORD`: La contraseña de tu usuario SQL Server activo.

*(Nota: Las variables de conexión de Docker como `DB_HOST` y `CELERY_BROKER_URL` ya están configuradas correctamente por defecto).*

## 🚀 Ejecución del Proyecto (Docker Compose)

El sistema levanta automáticamente el servidor web (Django), el worker asíncrono (Celery), el broker de mensajes (Redis) y prepara el entorno de procesamiento (FFmpeg) con un solo comando.

Abre tu terminal en la raíz del proyecto y ejecuta:
```bash
docker compose up --build
```
*(Nota: Tener en cuenta que debe estar configurada correctamente las variables de entorno .env para que corra el comando correctamente, La primera vez tomará algunos minutos mientras construye las imágenes y descarga las dependencias. Las ejecuciones posteriores serán casi inmediatas).*


## 🗄️ Migraciones de la Base de Datos
`Nota: Debes tener creada la base de datos y configurada en las variables de entorno .env`   
Una vez que los contenedores estén corriendo, debes preparar las tablas en tu SQL Server. Abre una nueva terminal (sin detener la que está corriendo Docker) y ejecuta:

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

## 📄 Documentación de la API
Cuando la terminal indique que los servicios están listos, puedes probar el sistema completo y acceder a la interfaz interactiva de la API (Swagger) visitando: 

👉 http://127.0.0.1:8000/swagger/