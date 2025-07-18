import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
        try:
            self.user = self.scope['user']
            self.socket_id = self.scope['url_route']['kwargs']['socket_id']
            # self.socket_id = "toto"

            # Vérifier si l'utilisateur est authentifié (optionnel)
            # if not self.user.is_authenticated:
            #     self.close(code=4001)  # Code d'erreur personnalisé pour non-authentifié
            #     return

            print(f"WebSocket connecting for socket_id: {self.socket_id}")

            # Add the socket to the group
            async_to_sync(self.channel_layer.group_add)(
                self.socket_id,
                self.channel_name
            )
            self.accept()
            print(f"WebSocket connection accepted for: {self.socket_id}")
            # await self.accept()

            # Update the is_connected field to True
        except Exception as e:
            print(f"Error during WebSocket connection: {e}")
            self.close(code=4000)  # Code d'erreur générique

        
        
    def disconnect(self, close_code):
    # async def disconnect(self, close_code):
        # Nettoyer le groupe avant la déconnexion
        async_to_sync(self.channel_layer.group_discard)(
                self.socket_id,
                self.channel_name
            )
        # Ne pas appeler self.close() ici - la déconnexion est déjà en cours
        print(f"WebSocket disconnected with code: {close_code}")
        # await self.close()
            
            # Update the is_connected field to False


    def receive(self, text_data):
        """
        Gérer les messages reçus du client pour maintenir la connexion active
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')

            if message_type == 'ping':
                # Répondre au ping pour maintenir la connexion
                self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif message_type == 'heartbeat':
                # Heartbeat pour vérifier que la connexion est active
                self.send(text_data=json.dumps({
                    'type': 'heartbeat_ack',
                    'status': 'alive'
                }))
            else:
                print(f"Message reçu: {data}")

        except json.JSONDecodeError:
            print(f"Message non-JSON reçu: {text_data}")
        except Exception as e:
            print(f"Erreur lors du traitement du message: {e}")

    def send_notification(self, event):
        message = event.get('message')
        type = event.get('my_type')
        data = event.get('data')
        my_event = event.get('event')
        self.send(text_data=json.dumps({
            'event': my_event,
            'type': type,
            'data': data,
            'message': message
        }))