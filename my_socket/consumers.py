import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
        self.user = self.scope['user']
        self.socket_id = self.scope['url_route']['kwargs']['socket_id']
        self.socket_id = "toto"
        # Add the socket to the group
        async_to_sync(self.channel_layer.group_add)(
            self.socket_id,
            self.channel_name
        )
        self.accept()
        # await self.accept()
        
        # Update the is_connected field to True

        
        
    def disconnect(self, close_code):
    # async def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
                self.socket_id,
                self.channel_name
            )
        self.close()
        # await self.close()
            
            # Update the is_connected field to False


    def receive(self, text_data):
        pass

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