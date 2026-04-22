import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from core.models import Usuari, Titol, UsuariTitol
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
class TestUsuariViewSet:
    def setup_method(self):
        self.client = APIClient()
        # Username únic per a aquest fitxer
        self.username = "user_viewset_test"
        self.user, _ = User.objects.get_or_create(username=self.username)
        self.usuari, _ = Usuari.objects.get_or_create(
            google_id="G_VIEWSET_UNIQUE",
            defaults={
                "username": self.username,
                "punts": 0,
                "pes": 60,
                "altura": 160,
                "ratxa": 0,
                "limitRutes": 5,
            },
        )
        self.client.force_authenticate(
            user=self.user, token={"google_id": "G_VIEWSET_UNIQUE"}
        )

    def test_retrieve_me_profile(self):
        url = "/api/usuaris/me/profile/"
        response = self.client.get(url)
        assert response.status_code == 200

    def test_get_usuari_titols(self):
        titol = Titol.objects.create(nom="Eco-Heroi")
        UsuariTitol.objects.get_or_create(usuari=self.usuari, titol=titol)
        url = f"/api/usuaris/{self.usuari.id}/titols/"
        response = self.client.get(url)
        assert response.status_code == 200

    def test_change_profile_pic_success(self):
        foto = SimpleUploadedFile("foto.jpg", b"content", content_type="image/jpeg")
        url = "/api/usuaris/me/profile-pic/"
        response = self.client.patch(url, {"profile_pic": foto}, format="multipart")
        assert response.status_code == 200

    def test_delete_account(self):
        url = "/api/usuaris/me/"
        response = self.client.delete(url)
        assert response.status_code == 204

    def test_search_usuaris(self):
        url = "/api/usuaris/"
        response = self.client.get(url, {"search": self.username})
        assert response.status_code == 200

    def test_action_usuario_no_encontrado(self):
        # Simulem un usuari que té token però no existeix a la DB d'Usuari
        self.client.force_authenticate(
            user=self.user, token={"google_id": "NONEXISTENT"}
        )
        url = "/api/usuaris/me/profile/"
        response = self.client.get(url)
        assert response.status_code == 404
