"""
ASGI config for votacion project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votacion.settings')

#Permitir peticiones http

django_asgi_app = get_asgi_application()

#Permitir canales y websockets

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import 
from channels
