from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import DadosImagem, ImagemUpload
from .utils import calcular_pontuacao


class ScoringTests(TestCase):
    def test_counts_only_matching_answers(self):
        self.assertEqual(calcular_pontuacao("abcde", "abzde"), 4)

    def test_returns_zero_for_missing_input(self):
        self.assertEqual(calcular_pontuacao("", "abc"), 0)
        self.assertEqual(calcular_pontuacao("abc", None), 0)


class DataModelTests(TestCase):
    def test_result_is_linked_to_user_and_uploaded_image(self):
        user = get_user_model().objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="strong-test-password",
        )
        image = ImagemUpload.objects.create(
            usuario=user,
            nome_arquivo="answer-sheet.png",
            conteudo=b"image-bytes",
            confirmada=True,
        )

        result = DadosImagem.objects.create(
            usuario=user,
            imagem=image,
            id_prova=1,
            id_participante=123,
            leitura="a" * 20,
            pontuacao=20,
        )

        self.assertEqual(result.usuario, user)
        self.assertEqual(result.imagem, image)
        self.assertEqual(result.pontuacao, 20)
