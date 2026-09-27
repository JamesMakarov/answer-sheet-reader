from django.contrib import admin
from django.urls import path, include  
from App.views import health_check, redirecionar_para_login

urlpatterns = [
    path('', redirecionar_para_login),
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
    path('auth/', include('App.urls')), 
    
]
