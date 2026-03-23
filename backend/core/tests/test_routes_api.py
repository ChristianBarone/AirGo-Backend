import pytest
from rest_framework.test import APIClient
from core.models import Route


@pytest.mark.django_db
class TestRouteAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = "/api/routes/"

    def test_llistar_rutes_buida(self):
        """Comprova que si no hi ha rutes, l'API retorna una llista buida []"""
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data == []

    def test_crear_i_llistar_ruta(self):
        """Creem una ruta a la BBDD i comprovem que l'API la retorna"""
        Route.objects.create(
            name="Ruta Diagonal",
            start_location="Maria Cristina",
            end_location="Glòries",
            distance=10.5,
            air_quality=15.0
        )

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['name'] == "Ruta Diagonal"

    def test_post_ruta_nova(self):
        """Simulem que el mòbil ens envia una ruta nova per guardar"""
        payload = {
            "name": "Ruta",
            "start_location": "FIB",
            "end_location": "Casa",
            "distance": 3.2,
            "air_quality": 5.0
        }
        response = self.client.post(self.url, payload, format='json')

        assert response.status_code == 201  # 201 = Created
        assert Route.objects.filter(name="Ruta").exists()

    def test_get_ruta_inexistent(self):
        """Si demanem una ruta que no existeix, ha de donar 404"""
        url_detall = f"{self.url}999/"  # Un ID que no existeix
        response = self.client.get(url_detall)
        assert response.status_code == 404