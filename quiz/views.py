import os
import tempfile
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from .models import VideoQuiz, Asignatura
from .tasks import procesar_video_gemini

@swagger_auto_schema(
    method='post',
    operation_description="Sube un video (.mp4) y extrae su audio para generar un cuestionario interactivo",
    manual_parameters=[
        openapi.Parameter(
            name='video',
            in_=openapi.IN_FORM,
            description='Archivo de video a analizar (Solo .mp4)',
            type=openapi.TYPE_FILE,
            required=True
        ),
        openapi.Parameter(
            name='num_preguntas',
            in_=openapi.IN_FORM,
            description='Cantidad de preguntas a generar a lo largo del video (Ej: 10, 15, 20)',
            type=openapi.TYPE_INTEGER,
            required=True 
        ),
        openapi.Parameter(
            name='asignatura_id',
            in_=openapi.IN_FORM,
            description='ID de la Asignatura a la que pertenece este video',
            type=openapi.TYPE_INTEGER,
            required=True 
        )
    ],
    responses={
        202: "Video aceptado y en proceso",
        400: "Error en la validación o formato incorrecto",
        404: "Asignatura no encontrada"
    }
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def generar_cuestionario(request):
    # --- VALIDACIÓN DE VIDEO ---
    if 'video' not in request.FILES:
        return Response({"error": "No se proporcionó ningún archivo de video en la clave 'video'."}, status=400)
    
    video_file = request.FILES['video']
    
    if not video_file.name.lower().endswith('.mp4'):
        return Response({
            "error": "Formato no admitido. Por favor, sube únicamente videos en formato .mp4"
        }, status=400)
    
    # --- VALIDACIÓN ESTRICTA DE NÚMERO DE PREGUNTAS ---
    if 'num_preguntas' not in request.data:
        return Response({"error": "El parámetro 'num_preguntas' es obligatorio."}, status=400)
        
    try:
        num_preguntas = int(request.data.get('num_preguntas'))
        if num_preguntas <= 0:
             return Response({"error": "La cantidad de preguntas debe ser mayor a cero."}, status=400)
    except (ValueError, TypeError):
        return Response({"error": "El parámetro 'num_preguntas' debe ser un número entero válido."}, status=400)
        
    # --- VALIDACIÓN DE ASIGNATURA ---
    asignatura_id = request.data.get('asignatura_id')
    asignatura_obj = None
    
    if asignatura_id:
        try:
            asignatura_obj = Asignatura.objects.get(id=asignatura_id)
        except Asignatura.DoesNotExist:
            return Response({"error": f"La asignatura con ID {asignatura_id} no existe en la base de datos."}, status=404)
    else:
        return Response({"error": "El parámetro 'asignatura_id' es obligatorio."}, status=400)

    # 1. Creamos el registro vinculando la Asignatura
    quiz_record = VideoQuiz.objects.create(
        video_name=video_file.name,
        status='PENDING',
        asignatura=asignatura_obj
    )
    # 2. Guardamos el video temporalmente en el servidor
    fd, temp_path = tempfile.mkstemp(suffix=".mp4")
    with os.fdopen(fd, 'wb') as f:
        for chunk in video_file.chunks():
            f.write(chunk)
            
    # 3. Mandamos la tarea a Celery de forma asíncrona
    procesar_video_gemini.delay(quiz_record.id, temp_path, num_preguntas)
    
    # 4. Devolvemos respuesta Inmediata al usuario
    return Response({
        "mensaje": "Video subido correctamente y encolado para procesamiento.",
        "id_registro": quiz_record.id,
        "asignatura": asignatura_obj.nombre,
        "preguntas_solicitadas": num_preguntas,
        "status": quiz_record.status
    }, status=202)


@swagger_auto_schema(
    method='get',
    operation_description="Consulta el estado de procesamiento de un video y obtiene el JSON si ya terminó",
    responses={
        200: "Estado actual y datos del cuestionario"
    }
)
@api_view(['GET'])
def consultar_estado_cuestionario(request, pk):
    quiz_record = get_object_or_404(VideoQuiz, pk=pk)
    
    asignatura_info = None
    if quiz_record.asignatura:
        asignatura_info = {
            "id": quiz_record.asignatura.id,
            "materia": quiz_record.asignatura.nombre,
            "carrera": quiz_record.asignatura.carrera.nombre
        }
    
    return Response({
        "id": quiz_record.id,
        "video_name": quiz_record.video_name,
        "info_academica": asignatura_info, 
        "status": quiz_record.status,
        "data": quiz_record.quiz_data,
        "error_message": quiz_record.error_message
    }, status=200)