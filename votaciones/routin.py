from django.urls import re_path
from . import consumers

# IMPORTANTE: Usar [ ] para que sea una lista y el nombre exacto de la clase
websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.ChatVotacionConsumer.as_asgi()),    
]