import os
import tempfile
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from .models import VideoQuiz
from .tasks import procesar_video_gemini

@swagger_auto_schema(
    method='post',
    operation_description="Sube un video (.mp4) y lo encola para generar un cuestionario interactivo usando IA",
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
        202: "Video aceptado y en proceso",
        400: "Error en la validación"
    }
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def generar_cuestionario(request):
    if 'video' not in request.FILES:
        return Response({"error": "No se proporcionó ningún archivo de video en la clave 'video'."}, status=400)
    
    video_file = request.FILES['video']
    
    # 1. Creamos el registro en SQL Server (Estado: PENDING)
    quiz_record = VideoQuiz.objects.create(
        video_name=video_file.name,
        status='PENDING'
    )
    
    # 2. Guardamos el archivo de forma temporal en el disco
    fd, temp_path = tempfile.mkstemp(suffix=".mp4")
    with os.fdopen(fd, 'wb') as f:
        for chunk in video_file.chunks():
            f.write(chunk)
            
    # 3. Mandamos la tarea a Celery de forma asíncrona usando .delay()
    procesar_video_gemini.delay(quiz_record.id, temp_path)
    
    # 4. Devolvemos respuesta Inmediata al usuario con el ID
    return Response({
        "mensaje": "Video subido correctamente y encolado para procesamiento.",
        "id_registro": quiz_record.id,
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
    
    return Response({
        "id": quiz_record.id,
        "video_name": quiz_record.video_name,
        "status": quiz_record.status,
        "data": quiz_record.quiz_data,
        "error_message": quiz_record.error_message
    }, status=200)