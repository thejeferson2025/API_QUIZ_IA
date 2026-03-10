import os
import time
import json
import tempfile
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv

# --- Importaciones nuevas de Django REST Framework y Swagger ---
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODELO_ELEGIDO = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=API_KEY)

class PreguntaInteractiva(BaseModel):
    segundo_de_pausa: int
    minuto_formateado: str
    pregunta: str
    opciones: list[str]
    respuesta_correcta: str

# --- Configuración de Swagger para este endpoint ---
@swagger_auto_schema(
    method='post',
    operation_description="Sube un video (.mp4) para generar un cuestionario interactivo usando IA",
    manual_parameters=[
        openapi.Parameter(
            name='video',
            in_=openapi.IN_FORM,
            description='Archivo de video a analizar',
            type=openapi.TYPE_FILE,
            required=True
        )
    ],
    responses={
        200: "Cuestionario generado con éxito",
        400: "Error en la validación del archivo",
        500: "Error interno o de procesamiento en la IA"
    }
)
@api_view(['POST']) # Reemplaza a @csrf_exempt
@parser_classes([MultiPartParser]) # Le dice a la API que espere archivos
def generar_cuestionario(request):
    
    if 'video' not in request.FILES:
        return Response({"error": "No se proporcionó ningún archivo de video en la clave 'video'."}, status=400)
    
    video_file = request.FILES['video']
    
    temp_path = ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        for chunk in video_file.chunks():
            temp_file.write(chunk)
        temp_path = temp_file.name

    try:
        video_upload = client.files.upload(file=temp_path)
        
        while video_upload.state.name == "PROCESSING":
            time.sleep(3)
            video_upload = client.files.get(name=video_upload.name)
            
        if video_upload.state.name == "FAILED":
            return Response({"error": "El procesamiento del video falló en los servidores de Google."}, status=500)

        prompt = """
        Eres un asistente educativo. Analiza este video detalladamente.
        Tu objetivo es crear una "lección interactiva" para mantener la concentración del estudiante.
        Genera 4 preguntas de opción múltiple. Cada pregunta debe estar anclada a un momento específico del video (un 'timestamp'). 
        La pregunta debe evaluar algo que se acaba de explicar en los segundos o minutos previos a ese timestamp.
        """
        
        response = client.models.generate_content(
            model=MODELO_ELEGIDO,
            contents=[video_upload, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[PreguntaInteractiva],
                temperature=0.2
            )
        )
        
        datos_json = json.loads(response.text)
        client.files.delete(name=video_upload.name)
        
        return Response({
            "mensaje": "Cuestionario generado con éxito",
            "data": datos_json
        }, status=200)

    except Exception as e:
        return Response({"error": f"Error interno: {str(e)}"}, status=500)
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)