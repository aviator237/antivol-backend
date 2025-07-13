import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from box.models import Box

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.socket_id = self.scope['url_route']['kwargs']['socket_id']
        
        # Add the socket to the group
        async_to_sync(self.channel_layer.group_add)(
            self.socket_id,
            self.channel_name
        )
        
        # Update the is_connected field to True
        try:
            box = Box.objects.get(socket_id=self.socket_id)
            box.is_connected = True
            box.save()
            self.accept()
        except Box.DoesNotExist:
            self.close()
        
        
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
                self.socket_id,
                self.channel_name
            )
            
            # Update the is_connected field to False
        try:
            box = Box.objects.get(socket_id=self.socket_id)
            box.is_connected = False
            box.save()
        except Box.DoesNotExist:
            pass
        # if self.user.is_authenticated:
            # Remove the socket from the group
            # async_to_sync(self.channel_layer.group_discard)(
            #     self.socket_id,
            #     self.channel_name
            # )
            
            # # Update the is_connected field to False
            # try:
            #     box = Box.objects.get(socket_id=self.socket_id)
            #     box.is_connected = False
            #     box.save()
            # except Box.DoesNotExist:
            #     pass
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