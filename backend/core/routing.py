from django.urls import re_path
from .consumers import ChatConsumer, ForumConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<other_id>\d+)/$", ChatConsumer.as_asgi()),
    re_path(r"^ws/forum/(?P<forum_id>\d+)/$", ForumConsumer.as_asgi()),
]
