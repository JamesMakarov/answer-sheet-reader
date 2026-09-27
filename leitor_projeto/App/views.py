import base64
import io
import logging
import os
from tempfile import NamedTemporaryFile

from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import connection
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .biblioteca import leitor_lib
from .forms import PerfilForm, RevisaoGabaritoForm
from .models import DadosImagem, ImagemUpload, Perfil
from .utils import GABARITOS, calcular_pontuacao

logger = logging.getLogger(__name__)

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ok"})
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)


def redirecionar_para_login(request):
    return redirect('login')


@login_required
def iniciar_leitura(request):
    if request.method == "POST":
        
        if request.FILES.get("imagem"):
            ImagemUpload.objects.filter(usuario=request.user, confirmada=False).delete()
            
            imagem_upload = request.FILES["imagem"]

            if not leitor_lib:
                return JsonResponse({"erro": -1, "mensagem": "Biblioteca não carregada"})

            try:
                imagem = Image.open(imagem_upload)
                buffer = io.BytesIO()
                imagem.save(buffer, format="PNG")
                buffer.seek(0)

                with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(buffer.read())
                    tmp_path = tmp.name

                resultado = leitor_lib.read_image_path(tmp_path.encode("utf-8"))
                leitura = resultado.leitura
                leitura_decodificada = leitura.decode("utf-8") if leitura else ""

                imagem_upload.seek(0)
                imagem_binaria = imagem_upload.read()
                imagem_obj = ImagemUpload.objects.create(
                    usuario=request.user,
                    nome_arquivo=imagem_upload.name,
                    conteudo=imagem_binaria,
                    confirmada=False
                )

                os.remove(tmp_path)

                form = RevisaoGabaritoForm(
                    leitura=leitura_decodificada,
                    initial={
                        'id_prova': resultado.id_prova,
                        'id_participante': resultado.id_participante
                    }
                )

                return render(request, 'revisar_leitura.html', {
                    'form': form,
                    'imagem_id': imagem_obj.id
                })

            except Exception:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
                logger.exception("Falha ao processar imagem de gabarito")
                return JsonResponse(
                    {"erro": -99, "mensagem": "Falha ao processar a imagem."},
                    status=500,
                )

        else:
            imagem_id = request.POST.get('imagem_id')
            imagem = get_object_or_404(ImagemUpload, pk=imagem_id, usuario=request.user)

            form = RevisaoGabaritoForm(request.POST)
            if form.is_valid():
                respostas = []
                for i in range(20):
                    valor = form.cleaned_data.get(f'questao_{i+1}', '')
                    respostas.append(valor if valor else 'x')

                leitura_str = ''.join(respostas)

                id_prova = form.cleaned_data['id_prova']
                gabarito = GABARITOS.get(id_prova)
                pontuacao = calcular_pontuacao(leitura_str, gabarito)

                DadosImagem.objects.create(
                    usuario=request.user,
                    imagem=imagem,
                    id_prova=id_prova,
                    id_participante=form.cleaned_data['id_participante'],
                    leitura=leitura_str,
                    pontuacao=pontuacao
                )

                imagem.confirmada = True
                imagem.save()

                messages.success(request, f"Leitura confirmada! Pontuação: {pontuacao}/20")
                return redirect('home')
            else:
                messages.error(request, "Erro ao salvar. Verifique os campos.")
                return render(request, 'revisar_leitura.html', {
                    'form': form,
                    'imagem_id': imagem_id
                })

    # <-- Aqui está a limpeza final -->
    ImagemUpload.objects.filter(usuario=request.user, confirmada=False).delete()
    return render(request, "upload.html")



User = get_user_model()

def login_view(request):
    if request.user.is_authenticated:
        messages.success(request, "Você já está logado!")
        return redirect('home')
    elif request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Credenciais inválidas.")
    return render(request, 'accounts/login.html')

def register_view(request):
    if request.user.is_authenticated:
        messages.success(request, "Você já está logado!")
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Este email já está em uso.")
        else:
            candidate = User(username=email, email=email)
            try:
                validate_password(password, user=candidate)
            except ValidationError as errors:
                for error in errors.messages:
                    messages.error(request, error)
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                )
                Perfil.objects.create(user=user)
                login(request, user)
                return redirect('home')

    return render(request, 'accounts/register.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def home_view(request):
    return render(request, 'accounts/home.html')

@login_required
def imagem_perfil(request, user_id):
    try:
        perfil = Perfil.objects.get(user_id=user_id)
        if not perfil.foto:
            raise Http404("Sem imagem")
        return HttpResponse(perfil.foto, content_type="image/png")
    except Perfil.DoesNotExist:
        raise Http404("Perfil não encontrado")


@login_required
def perfil_view(request):
    perfil = request.user.perfil

    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)

        foto_cropada = request.POST.get('foto_cropada')
        if foto_cropada and foto_cropada.startswith('data:image'):
            format, imgstr = foto_cropada.split(';base64,')
            perfil.foto = base64.b64decode(imgstr)

        if form.is_valid():
            form.save()
            return redirect('perfil')
    else:
        form = PerfilForm(instance=perfil)

    context = {
        'form': form,
        'perfil': perfil,
        'mostrar_formulario': True,
        'foto_base64': perfil.foto,
    }
    return render(request, 'accounts/perfil.html', context)





@login_required
def imagem_binaria(request, imagem_id):
    try:
        imagem = ImagemUpload.objects.get(pk=imagem_id, usuario=request.user)
        return HttpResponse(imagem.conteudo, content_type="image/png")  # ou "image/jpeg" conforme necessário
    except ImagemUpload.DoesNotExist:
        raise Http404("Imagem não encontrada")

@login_required
def galeria_usuario(request):
    ImagemUpload.objects.filter(usuario=request.user, confirmada=False).delete()
    imagens = ImagemUpload.objects.filter(usuario=request.user).order_by('-criado_em')
    
    return render(request, 'galeria.html', {'imagens': imagens})

@login_required
def dados_leituras(request):
    dados = DadosImagem.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'dados.html', {'dados':dados})

@login_required
def editar_dado(request, dado_id):
    dado = get_object_or_404(DadosImagem, pk=dado_id, usuario=request.user)

    if request.method == 'POST':
        # Reconstrói a leitura com base nas respostas enviadas no POST
        leitura_str = ''.join([request.POST.get(f'questao_{i+1}', '') for i in range(20)])
        
        # Repassa a leitura para o form, para manter os campos marcados
        form = RevisaoGabaritoForm(request.POST, leitura=leitura_str)

        if form.is_valid():
            respostas = []
            for i in range(20):
                valor = form.cleaned_data.get(f'questao_{i+1}', '')
                respostas.append(valor if valor else 'x')
            leitura_str = ''.join(respostas)

            id_prova = form.cleaned_data['id_prova']
            gabarito = GABARITOS.get(id_prova)
            pontuacao = calcular_pontuacao(leitura_str, gabarito)

            # Atualiza os dados
            dado.id_prova = id_prova
            dado.id_participante = form.cleaned_data['id_participante']
            dado.leitura = leitura_str
            dado.pontuacao = pontuacao
            dado.save()

            messages.success(request, f"Dados atualizados com sucesso! Nova pontuação: {pontuacao}/20")
            return redirect('dados_leituras')
    else:
        leitura_str = dado.leitura or ""
        form = RevisaoGabaritoForm(
            leitura=leitura_str,
            initial={
                'id_prova': dado.id_prova,
                'id_participante': dado.id_participante
            }
        )

    return render(request, 'editar_dado.html', {'form': form, 'dado': dado})



@login_required
def deletar_dado(request, dado_id):
    dado = get_object_or_404(DadosImagem, pk=dado_id, usuario=request.user)

    if request.method == 'POST':
        if dado.imagem:
            dado.imagem.delete()  # deleta a imagem associada primeiro
        dado.delete()             # depois deleta o dado
        messages.success(request, "Dado e imagem deletados com sucesso.")
        return redirect('dados_leituras')

    return render(request, 'confirmar_delete.html', {'dado': dado})

