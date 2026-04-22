import pytest

from core.models import Usuari
from core.serializers import UsuariSerializer, GoogleAuthSerializer
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
class TestSerializers:

    # UsuariSerializer

    def test_usuari_serializer_valid(self):
        data = {
            "username": "sportakus",
            "punts": 10,
            "pes": 90.0,
            "altura": 1.90,
            "ratxa": 1,
            "limitRutes": 10,
            "titol": "Novell",
        }
        serializer = UsuariSerializer(data=data)
        assert serializer.is_valid() is True

    def test_usuari_serializer_username_limit_inferior(self):
        data = {"username": "abc"}
        serializer = UsuariSerializer(data=data, partial=True)
        assert serializer.is_valid() is False
        assert "El username es demasiado corto" in str(serializer.errors["username"])

    def test_usuari_serializer_username_minim_acceptat(self):
        data = {"username": "abcd"}
        serializer = UsuariSerializer(data=data, partial=True)
        # pot fallar si falten altres camps obligatoris, per això usem partial=True
        serializer.is_valid()
        assert "username" not in serializer.errors

    @pytest.mark.django_db
    def test_usuari_serializer_get_profile_pic_url(self):
        user = Usuari.objects.create(
            username="ona", punts=0, pes=60, altura=160, ratxa=0, limitRutes=5
        )
        serializer = UsuariSerializer(user)
        # Si no hi ha imatge, retorna None
        assert serializer.data["profile_pic"] is None

    # def test_usuari_serializer_mida_imatge_limit(self):
    # mida_massa_gran = 2 * 1024 * 1024 + 1000
    # contingut_imatge_real = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    # imatge_falsa = SimpleUploadedFile(
    # "test.gif",
    # contingut_imatge_real + b"0" * mida_massa_gran,
    # content_type="image/gif"
    # )

    # serializer = UsuariSerializer(data={'profile_pic': imatge_falsa}, partial=True)
    # assert serializer.is_valid() is False
    # assert "La imagen no puede superar 2MB" in str(serializer.errors['profile_pic'])

    # GoogleAuthSerializer

    def test_google_auth_serializer_valid(self):
        serializer = GoogleAuthSerializer(data={"token": "un_token_qualsevol"})
        assert serializer.is_valid() is True

    def test_google_auth_serializer_missing_token(self):
        serializer = GoogleAuthSerializer(data={})
        assert serializer.is_valid() is False
        assert "token" in serializer.errors
