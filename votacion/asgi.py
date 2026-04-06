"""
ASGI config for votacion project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

# 1. Configurar el entorno de Django ANTES de importar los consumers
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votacion.settings')
django.setup()

# Importar el consumer después de django.setup() para evitar errores de carga
from votaciones.consumers import ChatVotacionConsumer

application = ProtocolTypeRouter({
    # Manejo de peticiones HTTP normales
    "http": get_asgi_application(),
    
    # Manejo de WebSockets con soporte para autenticación
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/chat/", ChatVotacionConsumer.as_asgi()),
        ])
    ),
})