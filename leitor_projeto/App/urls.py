from django.urls import path
from .views import iniciar_leitura, login_view, register_view, logout_view, home_view, perfil_view
from .views import galeria_usuario, imagem_binaria, dados_leituras, editar_dado, deletar_dado, imagem_perfil
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('upload/', iniciar_leitura, name="upload"), 
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('home/', home_view, name='home'),
    path('perfil/', perfil_view, name='perfil'),
    path('galeria/', galeria_usuario, name='galeria'),
    path('imagem/<int:imagem_id>/', imagem_binaria, name='imagem_binaria'),
    path('dados/', dados_leituras, name='dados_leituras'),
    path('dados/<int:dado_id>/editar/', editar_dado, name='editar_dado'),
    path('dados/<int:dado_id>/deletar/', deletar_dado, name='deletar_dado'),
    path('perfil/imagem/<int:user_id>/', imagem_perfil, name='imagem_perfil'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)