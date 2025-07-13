from enum import Enum


class SocketEvent(Enum):
    AUTHENTICATE = "authenticate"
    NOTIFICATION = "notification"
    TOKEN = "token"
    ACTION = "action"
    INVITATION = "invitation"

class SocketDataType(Enum):
    SHARE_PHOTO = "share_photo"
    CLOSE_WINDOW = 'close_window'
