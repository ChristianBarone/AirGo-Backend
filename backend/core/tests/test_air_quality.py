import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from core.services.air_quality import (
    calcular_aqi,
    haversine_km,
    get_latest_hour_value,
    get_air_quality_near,
)


@pytest.mark.django_db
class TestAirQualityAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = "/air-quality/"

    # TESTS UNITARIS
    def test_unit_calcular_aqi(self):
        # Cobertura de la taula completa d'umbrals
        assert calcular_aqi("PM10", 20) == 20
        assert calcular_aqi("PM2.5", 10) == 41  # Interpolació
        assert calcular_aqi("NO2", 100) == 117  # Interpolació
        assert calcular_aqi("O3", 150) == 163
        assert calcular_aqi("PM10", 400) == 300  # Valor màxim
        assert calcular_aqi("INVALID", 100) == 50  # Default
        assert calcular_aqi("PM10", "no-soc-un-numero") == 0  # Cas ValueError

    def test_unit_distancia_haversine(self):
        """Verifica el càlcul de distància geogràfica entre dos punts"""
        # Distància aproximada entre Pl. Catalunya i Sagrada Família
        dist = haversine_km(41.387, 2.170, 41.403, 2.174)
        assert 1.5 < dist < 2.5

    def test_unit_get_latest_hour(self):
        # Cas on l'última hora és la que té dades
        row = {"h24": "10", "h23": "5"}
        assert get_latest_hour_value(row) == "10"
        # Cas on hi ha buits
        row = {"h24": " ", "h23": None, "h22": "15"}
        assert get_latest_hour_value(row) == "15"
        # Cas buit total
        assert get_latest_hour_value({}) is None

    # TESTS D'INTEGRACIÓ
    @patch("core.services.air_quality.requests.get")
    def test_get_air_quality_integration(self, mock_get):
        """Simulem l'OpenData de la Generalitat i comprovem la resposta de l'API"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                "latitud": "41.38",
                "longitud": "2.17",
                "contaminant": "PM10",
                "nom_estacio": "Eixample",
                "h01": "25",
            }
        ]

        response = self.client.get(self.url, {"lat": 41.38, "lon": 2.17, "radio": 5})

        assert response.status_code == 200
        assert response.data[0]["zone"] == "Eixample"
        assert response.data[0]["aqi"] == 25

    @patch("core.services.air_quality.requests.get")
    def test_get_air_quality_near_filtering(self, mock_get):
        """Testejem el filtratge per radi i el 'pitjor AQI'"""
        mock_get.return_value.json.return_value = [
            # Estació a prop (0km) amb dos contaminants (ens hem de quedar el pitjor)
            {
                "latitud": "41.0",
                "longitud": "2.0",
                "contaminant": "PM10",
                "nom_estacio": "Estacio1",
                "h01": "10",
            },
            {
                "latitud": "41.0",
                "longitud": "2.0",
                "contaminant": "NO2",
                "nom_estacio": "Estacio1",
                "h01": "100",
            },
            # Estació lluny (fora de ràdio de 5km)
            {
                "latitud": "42.0",
                "longitud": "3.0",
                "contaminant": "PM10",
                "nom_estacio": "Lluny",
                "h01": "50",
            },
            {"latitud": "invalid", "longitud": "2.0"},
        ]

        results = get_air_quality_near(41.0, 2.0, radio_km=5)

        assert len(results) == 1
        assert results[0]["zone"] == "Estacio1"
        # L'AQI de NO2 (100 -> 111) és major que PM10 (10 -> 10)
        assert results[0]["aqi"] > 100
