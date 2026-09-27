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


class RegistrationTests(TestCase):
    def test_rejects_weak_password(self):
        response = self.client.post(
            "/auth/register/",
            {"email": "weak@example.com", "password": "123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(email="weak@example.com").exists())

    def test_creates_user_and_profile_with_valid_password(self):
        response = self.client.post(
            "/auth/register/",
            {
                "email": "new.user@example.com",
                "password": "A-strong-test-password-2026!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email="new.user@example.com")
        self.assertTrue(hasattr(user, "perfil"))


class HealthCheckTests(TestCase):
    def test_health_endpoint_reports_available_database(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
