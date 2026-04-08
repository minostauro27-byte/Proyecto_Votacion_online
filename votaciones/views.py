from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from votacion.firebase_config import initialize_firebase
from firebase_admin import firestore
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .authentication import FirebaseAuthentication
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Inicializar Base de Datos
db = initialize_firebase()

@method_decorator(csrf_exempt, name='dispatch')
class VotacionAPIView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def _actualizar_monitor(self, usuario_nombre="Sistema", candidato_nombre="N/A"):
        """Envía una señal al monitor para que se refresque vía WebSockets"""
        try:
            # Obtenemos el conteo actualizado para la gráfica
            docs = db.collection('api_votos').stream()
            conteo = {}
            for doc in docs:
                voto = doc.to_dict()
                cand = voto.get('candidato_id', 'Desconocido')
                conteo[cand] = conteo.get(cand, 0) + 1

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'sala_general', 
                {
                    'type': 'voto_update',
                    'conteo': conteo,
                    'voto_reciente': {
                        'usuario': usuario_nombre,
                        'candidato_id': candidato_nombre
                    }
                }
            )
        except Exception as e:
            print(f"Error en WebSocket: {e}")

    def post(self, request):
        """Registra un nuevo voto"""
        try:
            uid = request.user.uid
            email = request.user.email
            # Usamos el nombre del FirebaseUser o el email como fallback
            nombre = getattr(request.user, 'nombre', email)

            data = request.data.copy()
            data['usuario_id'] = uid
            data['usuario_nombre'] = nombre
            data['fecha'] = firestore.SERVER_TIMESTAMP
            data['estado'] = data.get('estado', 'En Revisión') # Estado por defecto

            # Guardar en Firestore
            doc_ref = db.collection('api_votos').add(data)
            
            # Notificar al monitor
            self._actualizar_monitor(nombre, data.get('candidato_id', 'Voto Registrado'))

            return Response({"mensaje": "Voto registrado con éxito", "id": doc_ref[1].id}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def put(self, request, pk=None):
        """Actualiza un voto (solo Admin o el dueño del voto)"""
        if not pk: return Response({"error": "ID requerido"}, status=400)
        try:
            doc_ref = db.collection('api_votos').document(pk)
            doc = doc_ref.get()
            if not doc.exists: return Response({"error": "No existe"}, status=404)
            
            voto_data = doc.to_dict()
            if request.user.rol != 'admin' and voto_data.get('usuario_id') != request.user.uid:
                return Response({"error": "Permiso denegado"}, status=403)

            doc_ref.update(request.data)
            
            nombre_admin = getattr(request.user, 'nombre', request.user.email)
            self._actualizar_monitor(nombre_admin, "Voto Editado")
            
            return Response({"mensaje": "Voto actualizado"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def delete(self, request, pk=None):
        """Elimina un voto"""
        if not pk: return Response({"error": "ID requerido"}, status=400)
        try:
            doc_ref = db.collection('api_votos').document(pk)
            doc = doc_ref.get()
            if not doc.exists: return Response({"error": "No existe"}, status=404)
            
            if request.user.rol != 'admin' and doc.to_dict().get('usuario_id') != request.user.uid:
                return Response({"error": "Permiso denegado"}, status=403)

            doc_ref.delete()
            self._actualizar_monitor("Sistema", "Voto eliminado")
            
            return Response({"mensaje": "Voto eliminado"}, status=204)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class EstaditicasAPIView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            rol = getattr(request.user, 'rol', 'usuario')
            
            docs = db.collection('api_votos').stream() 

            total = 0
            votos_verificados = 0
            conteo_candidatos = {}
            historial_completo = []

            
            for doc in docs:
                total += 1
                data = doc.to_dict()
                cand = data.get('candidato_id', 'N/A')
                estado = str(data.get('estado', '')).lower()

                # Sumatoria histórica para la gráfica
                conteo_candidatos[cand] = conteo_candidatos.get(cand, 0) + 1
                
                # Guardar para el historial visual del panel izquierdo
                historial_completo.append({
                    'usuario': data.get('usuario_nombre', data.get('usuario_id', 'Anónimo')),
                    'candidato': cand
                })

                if 'verificado' in estado:
                    votos_verificados += 1

            # Calculamos el porcentaje global
            porcentaje = int((votos_verificados / total) * 100) if total > 0 else 0

            return Response({
                'votos_verificados': votos_verificados,
                'total': total,
                'porcentaje': porcentaje,
                'conteo_candidatos': conteo_candidatos,
                'historial_inicial': historial_completo # Esto envía los votos viejos
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
# Al final de views.py
def Monitor_view(request):
    return render(request, 'prueba_final.html') # Asegúrate que el nombre del HTML sea correcto