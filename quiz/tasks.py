import os
import json
import time
import subprocess
from celery import shared_task
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
from .models import VideoQuiz

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODELO_ELEGIDO = os.getenv("GEMINI_MODEL")

client = genai.Client(api_key=API_KEY)

class PreguntaInteractiva(BaseModel):
    segundo_de_pausa: int
    minuto_formateado: str
    pregunta: str
    opciones: list[str]
    respuesta_correcta: str

def comprimir_video_ffmpeg(input_path):
    """
    Comprime el video a 360p, 2 fotogramas por segundo, preservando el audio original.
    Devuelve la ruta del nuevo archivo comprimido.
    """
    # Generamos un nuevo nombre para el archivo comprimido
    output_path = input_path.replace('.mp4', '_comprimido.mp4')
    
    # Comando mágico de FFmpeg
    comando = [
        'ffmpeg',
        '-y',                 # Sobrescribir si existe
        '-i', input_path,     # Archivo de entrada
        '-vf', 'scale=-2:360',# Reducir resolución a 360p (mantiene proporción)
        '-r', '2',            # Bajar a 2 FPS (Gemini no necesita más para entender el contexto)
        '-c:v', 'libx264',    # Codec de video estándar
        '-preset', 'ultrafast',# Comprimir lo más rápido posible, sin importar si no es "perfecto"
        '-crf', '28',         # Calidad visual baja (ahorra mucho peso)
        '-c:a', 'copy',       # COPIAR el audio original (esencial para no perder tiempo re-codificando el audio)
        output_path
    ]
    
    try:
        # Ejecutamos el comando en la consola de forma silenciosa
        subprocess.run(comando, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except subprocess.CalledProcessError as e:
        # Si FFmpeg falla, lanzamos el error con los detalles
        error_msg = e.stderr.decode('utf-8')
        raise Exception(f"Error comprimiendo el video con FFmpeg: {error_msg}")


@shared_task
def procesar_video_gemini(video_quiz_id, file_path):
    quiz_record = VideoQuiz.objects.get(id=video_quiz_id)
    quiz_record.status = 'PROCESSING'
    quiz_record.save()

    compressed_file_path = None

    try:
        # 1. Comprimimos el video primero
        compressed_file_path = comprimir_video_ffmpeg(file_path)
        
        # 2. Subimos el video COMPRIMIDO a Gemini
        video_upload = client.files.upload(file=compressed_file_path)
        
        # 3. Esperamos a que Google procese el video
        while video_upload.state.name == "PROCESSING":
            time.sleep(5) 
            video_upload = client.files.get(name=video_upload.name)
            
        if video_upload.state.name == "FAILED":
            raise Exception("El procesamiento del video falló en los servidores de Google.")

        # 4. Generamos el contenido
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
        
        try:
            client.files.delete(name=video_upload.name)
        except:
            pass
        
        # 5. Guardamos el resultado exitoso
        quiz_record.quiz_data = datos_json
        quiz_record.status = 'COMPLETED'
        quiz_record.save()

    except Exception as e:
        quiz_record.status = 'FAILED'
        quiz_record.error_message = str(e)
        quiz_record.save()
    
    finally:
        # Limpieza: Borramos el original Y el comprimido de tu disco duro
        if os.path.exists(file_path):
            os.remove(file_path)
        if compressed_file_path and os.path.exists(compressed_file_path):
            os.remove(compressed_file_path)