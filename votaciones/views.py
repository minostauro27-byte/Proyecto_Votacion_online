from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import VotoSerializer
from votacion.firebase_config import initialize_firebase
from firebase_admin import firestore
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .authentication import FirebaseAuthentication
from drf_spectacular.utils import extend_schema # Añadido para Swagger

db=initialize_firebase

@method_decorator(csrf_exempt, name='dispatch')
class VotacionAPIView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

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
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        
        serializer = VotoSerializer(data=request.data)
        if serializer.is_valid():
            datos_validados = serializer.validated_data
            datos_validados['usuario_id'] = request.user.uid
            datos_validados['fecha_voto'] = firestore.SERVER_TIMESTAMP
            try:
                nuevo_voto = db.collection('api_votos').add(datos_validados)
                return Response({"mensaje": "Voto registrado", "id": nuevo_voto[1].id}, status=201)
            except Exception as e:
                return Response({"Error": str(e)}, status=500)
        return Response(serializer.errors, status=400)
 
    def put(self, request, pk=None):
        """Actualizar un voto"""
        if not pk: return Response({"error": "ID requerido"}, status=400)
        try:
            doc_ref = db.collection('api_votos').document(pk)
            # Solo actualizamos si el usuario es dueño o admin
            doc = doc_ref.get()
            if not doc.exists: return Response({"error": "No existe"}, status=404)
            if request.user.rol != 'admin' and doc.to_dict().get('usuario_id') != request.user.uid:
                return Response({"error": "Permiso denegado"}, status=403)

            doc_ref.update(request.data)
            return Response({"mensaje": "Voto actualizado"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def delete(self, request, pk=None):
        """Eliminar un voto"""
        if not pk: return Response({"error": "ID requerido"}, status=400)
        try:
            doc_ref = db.collection('api_votos').document(pk)
             
            doc = doc_ref.get()
            if not doc.exists: return Response({"error": "No existe"}, status=404)
            if request.user.rol != 'admin' and doc.to_dict().get('usuario_id') != request.user.uid:
                return Response({"error": "Permiso denegado"}, status=403)

            doc_ref.delete()
            return Response({"mensaje": "Voto eliminado"}, status=204)
        except Exception as e:
            return Response({"error": str(e)}, status=500)