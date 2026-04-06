import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatVotacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'sala_general'
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        # 1. Cargar historial de Firebase al conectar
        try:
            from votacion.firebase_config import initialize_firebase
            db = initialize_firebase()
            # Traemos el historial (puedes quitar .order_by si da error de índice)
            docs = db.collection('api_votos').stream()
            
            conteo = {}
            historial_detallado = []
            
            for doc in docs:
                voto = doc.to_dict()
                cand = voto.get('candidato', 'N/A')
                user = voto.get('usuario_nombre', 'Anónimo')
                
                conteo[cand] = conteo.get(cand, 0) + 1
                historial_detallado.append({'usuario': user, 'candidato': cand})

            # Enviamos el estado inicial solo al que se conecta
            await self.send(text_data=json.dumps({
                'tipo': 'estado_inicial',
                'conteo': conteo,
                'historial': historial_detallado
            }))
        except Exception as e:
            print(f"Error en connect: {e}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        # Lógica del Chat: Recibe del JS y rebota al grupo
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'mensaje': data.get('mensaje', ''),
                'usuario': data.get('usuario', 'Anónimo')
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'tipo': 'chat',
            'mensaje': event['mensaje'],
            'usuario': event['usuario']
        }))

    async def voto_update(self, event):
        # Recibe datos de views.py y los manda al monitor
        await self.send(text_data=json.dumps({
            'tipo': 'nuevo_voto',
            'conteo': event['conteo'],
            'detalle': event['voto_reciente']
        }))