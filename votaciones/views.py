from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from .serializers import VotoSerializer
from votacion.firebase_config import initialize_firebase
from firebase_admin import firestore
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .authentication import FirebaseAuthentication
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Ejecutamos la función para tener el objeto de la DB listo
db = initialize_firebase()

@method_decorator(csrf_exempt, name='dispatch')
class VotacionAPIView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def _actualizar_monitor(self, usuario_nombre="Sistema", candidato_nombre="N/A"):
        """Función auxiliar para refrescar el monitor en tiempo real"""
        try:
            docs = db.collection('api_votos').stream()
            conteo = {}
            for doc in docs:
                voto = doc.to_dict()
                cand = voto.get('candidato', 'Desconocido')
                conteo[cand] = conteo.get(cand, 0) + 1

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'sala_general', 
                {
                    'type': 'voto_update',
                    'conteo': conteo,
                    'voto_reciente': {
                        'usuario': usuario_nombre,
                        'candidato': candidato_nombre
                    }
                }
            )
        except Exception as e:
            print(f"Error actualizando socket: {e}")

    def get(self, request, pk=None):  
        uid_usuario = request.user.uid
        rol_usuario = request.user.rol
        try: 
            if pk:
                doc = db.collection('api_votos').document(pk).get()
                if not doc.exists:
                    return Response({"error": "Voto no encontrado"}, status=404)
                return Response(doc.to_dict(), status=200)

            query = db.collection('api_votos')
            if rol_usuario != 'admin':
                query = query.where('usuario_id', '==', uid_usuario)
            
            docs = query.stream()
            votos = [{'id': doc.id, **doc.to_dict()} for doc in docs]
            return Response({"rol": rol_usuario, "datos": votos}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"Error": str(e)}, status=500)

    def post(self, request):
        serializer = VotoSerializer(data=request.data)
        if serializer.is_valid():
            datos_validados = serializer.validated_data
            
            # Extraemos info del usuario autenticado
            nombre_usuario = getattr(request.user, 'username', 'Usuario') 
            datos_validados['usuario_id'] = request.user.uid
            datos_validados['usuario_nombre'] = nombre_usuario # Guardamos el nombre para el historial
            datos_validados['fecha_voto'] = firestore.SERVER_TIMESTAMP
            
            try:
                nuevo_voto = db.collection('api_votos').add(datos_validados)
                
                # Disparamos actualización al Monitor
                self._actualizar_monitor(nombre_usuario, datos_validados['candidato'])

                return Response({"mensaje": "Voto registrado", "id": nuevo_voto[1].id}, status=201)
            except Exception as e:
                return Response({"Error": str(e)}, status=500)
        return Response(serializer.errors, status=400)

    def put(self, request, pk=None):
        if not pk: return Response({"error": "ID requerido"}, status=400)
        try:
            doc_ref = db.collection('api_votos').document(pk)
            doc = doc_ref.get()
            if not doc.exists: return Response({"error": "No existe"}, status=404)
            
            if request.user.rol != 'admin' and doc.to_dict().get('usuario_id') != request.user.uid:
                return Response({"error": "Permiso denegado"}, status=403)

            doc_ref.update(request.data)
            
            # Actualizamos el monitor para que la gráfica refleje el cambio
            self._actualizar_monitor(request.user.username, "Cambio de voto")
            
            return Response({"mensaje": "Voto actualizado"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def delete(self, request, pk=None):
        if not pk: return Response({"error": "ID requerido"}, status=400)
        try:
            doc_ref = db.collection('api_votos').document(pk)
            doc = doc_ref.get()
            if not doc.exists: return Response({"error": "No existe"}, status=404)
            
            if request.user.rol != 'admin' and doc.to_dict().get('usuario_id') != request.user.uid:
                return Response({"error": "Permiso denegado"}, status=403)

            doc_ref.delete()
            
            # Notificamos al monitor que un voto desapareció
            self._actualizar_monitor("Sistema", "Voto eliminado")
            
            return Response({"mensaje": "Voto eliminado"}, status=204)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# Vista para el monitor (Asegúrate que el nombre coincida en urls.py)
def Monitor_view(request):
    return render(request, 'prueba_final.html')