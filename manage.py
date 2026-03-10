#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading
import socket
import time
import webbrowser

def wait_and_open_browser():
    """Espera a que el puerto 8000 esté abierto y luego lanza el navegador."""
    url = 'http://127.0.0.1:8000/swagger/'
    
    # Intentamos conectarnos al puerto continuamente hasta que responda
    while True:
        try:
            # Intenta crear una conexión interna al puerto 8000
            with socket.create_connection(('127.0.0.1', 8000), timeout=0.5):
                break  # ¡Conexión exitosa! El servidor de Django ya está listo.
        except (ConnectionRefusedError, TimeoutError, OSError):
            # Si el servidor aún no levanta, esperamos 0.2 segundos y volvemos a intentar
            time.sleep(0.2)
            
    # Una vez que el bucle termina (el puerto está abierto), abrimos el navegador
    webbrowser.open(url)

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gemini_api.settings')

    # Si el comando es runserver y NO estamos en el proceso de auto-recarga
    if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
        # Iniciamos nuestro verificador de puerto en segundo plano
        threading.Thread(target=wait_and_open_browser, daemon=True).start()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()