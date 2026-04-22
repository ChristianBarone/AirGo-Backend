from core.views.route_pollution_view import generar_segments_contaminacio, haversine
from core.services.navigation import get_eco_route as get_eco_service
from unittest.mock import patch


def test_haversine_logic():
    # Distància entre dos punts iguals ha de ser 0
    assert haversine(41.0, 2.0, 41.0, 2.0) == 0


def test_generar_segments_logic():
    punts = [[2.0, 41.0], [2.001, 41.001], [2.1, 41.1]]
    estacions = [{"geoPoint": {"lat": 41.0, "lon": 2.0}, "aqi": 80}]
    # El primer punt està a prop de l'estació (AQI 80)
    # el segon també, el tercer no (AQI 0)
    segments = generar_segments_contaminacio(punts, estacions, radi_km=0.5)

    assert len(segments) >= 1
    assert segments[0][2] == 80  # El valor d'AQI detectat


@patch("core.services.navigation.requests.post")
def test_navigation_service_error_handling(mock_post):
    """Prova el tractament d'errors de GraphHopper"""
    mock_post.return_value.status_code = 400
    mock_post.return_value.text = "Bad Request"

    res = get_eco_service({"lat": 41, "lon": 2}, {"lat": 41.1, "lon": 2.1}, [])
    assert "error" in res
