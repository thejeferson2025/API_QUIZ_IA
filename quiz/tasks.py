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
MODELO_ELEGIDO = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=API_KEY)

class PreguntaInteractiva(BaseModel):
    segundo_de_pausa: int
    minuto_formateado: str
    pregunta: str
    opciones: list[str]
    respuesta_correcta: str

def extraer_audio_ffmpeg(input_path):
    """
    Extrae únicamente la pista de audio del video y la guarda como MP3.
    """
    # Generamos el nombre del archivo de salida pero con extensión .mp3
    output_path = input_path.replace('.mp4', '.mp3')
    
    comando = [
        'ffmpeg',
        '-y',                 # Sobrescribir si existe
        '-i', input_path,     # Archivo de entrada (.mp4)
        '-q:a', '0',          # Mantener la mejor calidad de audio posible
        '-map', 'a',          # Mapear/Extraer SOLO el canal de audio
        output_path
    ]
    
    try:
        subprocess.run(comando, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8')
        raise Exception(f"Error extrayendo el audio con FFmpeg: {error_msg}")

@shared_task
def procesar_video_gemini(video_quiz_id, file_path, num_preguntas=4):
    quiz_record = VideoQuiz.objects.get(id=video_quiz_id)
    
    # --- ESCUDO PROTECTOR CONTRA EJECUCIONES FANTASMAS ---
    if quiz_record.status == 'COMPLETED':
        return "El video ya fue procesado exitosamente. Evitando re-ejecución."
    # -----------------------------------------------------

    # Limpiamos posibles errores anteriores si es un reintento legítimo
    quiz_record.status = 'PROCESSING'
    quiz_record.error_message = None 
    quiz_record.save()

    audio_file_path = None

    try:
        audio_file_path = extraer_audio_ffmpeg(file_path)
        file_upload = client.files.upload(file=audio_file_path)
        
        while file_upload.state.name == "PROCESSING":
            time.sleep(3) 
            file_upload = client.files.get(name=file_upload.name)
            
        if file_upload.state.name == "FAILED":
            raise Exception("El procesamiento del archivo falló en los servidores de Google.")

        prompt = f"""
        Eres un asistente educativo. A continuación recibirás la grabación de audio completa de una clase.
        Tu objetivo es crear una "lección interactiva" para mantener la concentración del estudiante.
        Genera EXACTAMENTE {num_preguntas} preguntas de opción múltiple. 
        
        REGLA CRÍTICA DE DISTRIBUCIÓN:
        Las preguntas DEBEN estar distribuidas cronológicamente y de manera uniforme a lo largo de TODO el tiempo que dura el audio.
        NO agrupes las preguntas en los primeros minutos.
        
        Instrucción estricta: Divide mentalmente la duración total del audio en {num_preguntas} fragmentos de tiempo iguales. Debes extraer exactamente una (1) pregunta del tema principal hablado en cada uno de esos fragmentos. 
        Por ejemplo, si pido 3 preguntas, saca una del inicio, una del medio y una del final.
        
        Cada pregunta debe estar anclada al momento exacto (timestamp) donde se dio la explicación en el audio.
        """
        
        response = client.models.generate_content(
            model=MODELO_ELEGIDO,
            contents=[file_upload, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[PreguntaInteractiva],
                temperature=0.2 
            )
        )
        
        datos_json = json.loads(response.text)
        
        try:
            client.files.delete(name=file_upload.name)
        except:
            pass
        
        quiz_record.quiz_data = datos_json
        quiz_record.status = 'COMPLETED'
        quiz_record.save()

    except Exception as e:
        quiz_record.status = 'FAILED'
        quiz_record.error_message = str(e)
        quiz_record.save()
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if audio_file_path and os.path.exists(audio_file_path):
            os.remove(audio_file_path)