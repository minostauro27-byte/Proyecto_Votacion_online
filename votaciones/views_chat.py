from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .authentication import FirebaseAuthentication 
from votacion.firebase_config import initialize_firebase

db = initialize_firebase()


class ChatHistorialAPIView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            mensaje_ref = (
                db.collection("api_chat_mensajes")
                .order_by("timestamp", direction="DESCENDING")
                .limit(20)
                .stream()
            )

            historial = []

            for doc in mensaje_ref:
                data = doc.to_dict()
                historial.append({
                    "id": doc.id,
                    "usuario": data.get("usuario"),
                    "mensaje": data.get("mensaje"),
                    "timestamp": data.get("timestamp"),
                })

            return Response(historial, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )