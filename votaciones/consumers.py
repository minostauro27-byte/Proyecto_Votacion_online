import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

class ChatVotacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'sala_general'
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        # 1. Obtener la base de datos (Llamando a la función con paréntesis)
        from votacion.firebase_config import initialize_firebase
        db = initialize_firebase()
        
        # 2. Consultar historial completo de Firebase
        docs = db.collection('api_votos').order_by('fecha_voto').stream()
        
        conteo = {}
        historial_detallado = []
        
        for doc in docs:
            voto = doc.to_dict()
            cand = voto.get('candidato', 'N/A')
            user = voto.get('usuario_nombre', 'Anónimo') # Asegúrate de guardar el nombre al votar
            
            # Sumar al total
            conteo[cand] = conteo.get(cand, 0) + 1
            # Agregar al log detallado
            historial_detallado.append({'usuario': user, 'candidato': cand})

        # 3. Enviar estado inicial al usuario que se acaba de conectar
        await self.send(text_data=json.dumps({
            'tipo': 'estado_inicial',
            'conteo': conteo,
            'historial': historial_detallado
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
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
        # Este recibe los datos en tiempo real desde views.py
        await self.send(text_data=json.dumps({
            'tipo': 'nuevo_voto',
            'conteo': event['conteo'],
            'detalle': event['voto_reciente']
        }))