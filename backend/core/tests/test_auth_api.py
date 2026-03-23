import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestGoogleAuthAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = "/auth/google/"

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_login_google_crea_usuari_si_no_existeix(self, mock_google):
        """
        Simulem que Google ens diu que el token és vàlid.
        Comprovem que el Backend crea l'usuari i retorna el JWT.
        """
        mock_google.return_value = {
            'email': 'sportakus@gmail.com',
            'name': 'Sportakus',
            'picture': 'http://imatge.com/foto.jpg',
            'email_verified': True
        }

        response = self.client.post(self.url, {'token': 'token_de_mentida'}, format='json')

        assert response.status_code == 200
        assert response.data['user'] == 'sportakus@gmail.com'
        assert 'access' in response.data

        assert User.objects.filter(email='sportakus@gmail.com').exists()

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_login_google_falla_si_token_es_invalid(self, mock_google):
        """Simulem que Google diu que el token ha caducat o és fals"""
        mock_google.side_effect = ValueError("Token expired")

        response = self.client.post(self.url, {'token': 'token_caducat'}, format='json')

        assert response.status_code == 400
        assert "Invalid Google token" in response.data['error']

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_login_google_falla_si_email_no_verificat(self, mock_google):
        """Simulem un usuari de Google que no ha confirmat el seu correu"""
        mock_google.return_value = {
            'email': 'sportakus@gmail.com',
            'email_verified': False
        }

        response = self.client.post(self.url, {'token': 'token_valid'}, format='json')

        assert response.status_code == 400
        assert response.data['error'] == "Email not verified"