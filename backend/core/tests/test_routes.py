import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from core.models import BicingEstacio
from django.contrib.auth.models import User
from core.services.bicing import extract_station_name, get_bicing_near
import requests


@pytest.mark.django_db
class TestBicingAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = "/bicing/"
        self.user = User.objects.create_user(username="tester", password="pass123")
        self.client.force_authenticate(user=self.user)

    def test_extract_station_name_logic(self):
        assert extract_station_name("Sants", "ca") == "Sants"
        names = [
            {"language": "ca", "text": "Català"},
            {"language": "es", "text": "Cast"},
        ]
        assert extract_station_name(names, "ca") == "Català"
        assert extract_station_name(names, "en") == "Cast"  # Fallback es
        assert extract_station_name([], "ca") == ""

    @patch("core.services.bicing.get_stations_info")
    @patch("core.services.bicing.get_stations_status")
    def test_get_bicing_near_integration(self, mock_status, mock_info):
        mock_info.return_value = [
            {"station_id": 1, "name": "Test", "lat": 41.0, "lon": 2.0}
        ]
        mock_status.return_value = {
            "1": {
                "num_bikes_available_types": {"mechanical": 5},
                "status": "IN_SERVICE",
            }
        }

        res = get_bicing_near(41.0, 2.0, radio_km=1)
        assert len(res) == 1
        assert res[0]["name"] == "Test"

    def test_bicing_fallback_database(self):
        BicingEstacio.objects.create(
            station_id=123,
            name="Estacio Local",
            lat=41.3,
            lon=2.1,
            capacity=20,
            bikes_available=10,
            docks_available=10,
        )
        # Usem requests.exceptions.RequestException
        # perquè el servei és el que atrapa
        with patch(
            "core.services.bicing.requests.get",
            side_effect=requests.exceptions.RequestException,
        ):
            response = self.client.get(self.url, {"lat": 41.3, "lon": 2.1})
            assert response.status_code == 200
            assert response.data[0]["name"] == "Estacio Local"
