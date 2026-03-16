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

# Inicializamos Firebase
db = initialize_firebase()

@method_decorator(csrf_exempt, name='dispatch')
class VotacionAPIView(APIView):
    """
    Vista para gestionar votos con autenticación Firebase.
    El decorador @csrf_exempt permite peticiones externas sin token CSRF.
    """
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated] # Asegura que el usuario tenga un token válido

    @extend_schema(
        summary="Listar votos",
        description="Listar votos (Administrador ve todos, Votante ve solo los suyos)",
        responses={200: VotoSerializer(many=True)}
    )
    def get(self, request):
        """
        Listar votos (Administrador ve todos, Votante ve solo los suyos)
        """
        # Aquí 'request.user' existe gracias a FirebaseAuthentication
        uid_usuario = request.user.uid
        rol_usuario = request.user.rol

        try:
            query = db.collection('api_votos')

            # Si no eres admin, filtra por tu propio ID
            if rol_usuario != 'admin':
                query = query.where('usuario_id', '==', uid_usuario)

            docs = query.stream()
            votos = [{'id': doc.id, **doc.to_dict()} for doc in docs]

            return Response({"rol": rol_usuario, "datos": votos}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)