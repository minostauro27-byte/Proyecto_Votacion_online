from django.urls import path
from .views_auth import RegistroAPIView, LoginApiView
from .views_perfil import PerfilImagenAPIView
from .views_chat import ChatHistorialAPIView
from .views import VotacionAPIView, EstaditicasAPIView, Monitor_view 
from django.shortcuts import render

urlpatterns = [
   path('registro/', lambda r: render(r, 'registro.html'), name="view_registro"),
    path('login/', lambda r: render(r, 'login.html'), name="view_login"),
    path('votos/votar/', lambda r: render(r, 'votar.html'), name="view_votar"),
    path('monitor/', Monitor_view, name="monitor_realtime"),

    path('auth/registro/', RegistroAPIView.as_view(), name="api_registro"),
    path('auth/login/', LoginApiView.as_view(), name="api_login"),

    
    path('votos/', VotacionAPIView.as_view(), name="api_votos_lista"),
    path('votos/estadisticas/', EstaditicasAPIView.as_view(), name="api_votos_estadisticas"),
    path('votos/<str:pk>/', VotacionAPIView.as_view(), name="api_votos_detalle"),

    

    path('votos/perfil/imagen/', PerfilImagenAPIView.as_view(), name="api_perfil_foto"),
    path('chat/historial/', ChatHistorialAPIView.as_view(), name="chat_historial"),
]