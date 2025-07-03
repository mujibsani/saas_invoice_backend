from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Notification
from .serializers import NotificationSerializer


class UserNotificationsView(generics.ListAPIView):
    """✅ Fetch user notifications and mark them as read when accessed."""
    authentication_classes = [JWTAuthentication]
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """✅ Users only see their own notifications."""
        notifications = Notification.objects.filter(user=self.request.user).order_by("-created_at")
        
        # Mark notifications as read
        notifications.update(is_read=True)
        
        return notifications


class UnreadNotificationsCountView(APIView):
    """✅ Get count of unread notifications."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count})
