from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/users/', include('invoice_expense.urls')),
<<<<<<< HEAD
    # path('api/users/', include('tasks.urls')),
=======
    path('api/users/', include('tasks.urls')),
>>>>>>> cc96dc17c44ba98fa1bd0bddf3d97ae1611c7293
    # path('auth/', include('djoser.urls')),
]
# Serve media files in development
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)