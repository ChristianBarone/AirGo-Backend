package com.graphhopper.routing.util;

import com.fasterxml.jackson.databind.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.*;

public class PollutionService {
    private static final Logger logger = LoggerFactory.getLogger(PollutionService.class);

    private static class PollutionPoint {
        double lat, lon, value;

        PollutionPoint(double lat, double lon, double value) {
            this.lat = lat;
            this.lon = lon;
            this.value = value;
        }
    }

    private List<PollutionPoint> points = new ArrayList<>();

    public PollutionService() {
        loadData();
    }

    private double safeParse(String s) {
        if (s == null || s.isEmpty()) return 0;
        try {
            return Double.parseDouble(s);
        } catch (Exception e) {
            return 0;
        }
    }

    private double getMaxPollutionDoubleFromStrings(String h01,  String h02, String h03, String h04) {
        double d1 = safeParse(h01);
        double d2 = safeParse(h02);
        double d3 = safeParse(h03);
        double d4 = safeParse(h04);
        return Math.max(d1, Math.max(d2, Math.max(d3, d4)));
    }

    // 🔹 Nueva lógica de normalización más sensible
    private double normalizarAQI(int aqi) {
        // En lugar de una división lineal, usamos una curva que
        // resalte los valores mediocres y malos.
        if (aqi <= 50) return 0.05;  // Aire limpio: casi nada de penalización
        if (aqi <= 100) return 0.4;  // Moderado: penalización notable
        if (aqi <= 200) return 0.8;  // Malo: penalización muy alta
        return 1.0;                  // Muy malo: evitar a toda costa
    }

    // 🔹 Cargar JSON (Ajustado)
    private void loadData() {
        try {
            ObjectMapper mapper = new ObjectMapper();
            // Cambiamos el File para que busque en una ruta más flexible si es necesario
            File jsonFile = new File("pollution.json");
            if (!jsonFile.exists()) {
                logger.info("CRÍTICO: No existe el archivo pollution.json en " + jsonFile.getAbsolutePath());
                return;
            }

            List<Map<String, Object>> data = mapper.readValue(jsonFile, List.class);
            Map<String, PollutionPoint> estaciones = new HashMap<>();

            for (Map<String, Object> station : data) {
                try {
                    // Usamos toString().trim() para evitar errores de tipo
                    double lat = Double.parseDouble(station.get("latitud").toString());
                    double lon = Double.parseDouble(station.get("longitud").toString());
                    String contaminant = (String) station.get("contaminant");

                    double valor = getMaxPollutionDoubleFromStrings(
                            station.getOrDefault("h01", "0").toString(),
                            station.getOrDefault("h02", "0").toString(),
                            station.getOrDefault("h03", "0").toString(),
                            station.getOrDefault("h04", "0").toString()
                    );

                    int aqi = calcularAQI(contaminant, valor);
                    double normalized = normalizarAQI(aqi); // <--- Nueva función

                    String stationId = lat + "," + lon;
                    if (!estaciones.containsKey(stationId) || normalized > estaciones.get(stationId).value) {
                        estaciones.put(stationId, new PollutionPoint(lat, lon, normalized));
                    }
                } catch (Exception e) {
                    // logger.info("Error procesando estación: " + e.getMessage());
                }
            }
            points.addAll(estaciones.values());
            logger.info("SUCCESS: Cargadas " + points.size() + " estaciones de polución.");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private int calcularAQI(String contaminant, double valor) {
        if (contaminant == null) return 50;

        switch (contaminant) {
            case "PM10":
                if (valor <= 50) return 50;
                if (valor <= 100) return 100;
                if (valor <= 250) return 200;
                return 300;

            case "NO2":
                if (valor <= 40) return 50;
                if (valor <= 90) return 100;
                return 200;

            default:
                return 50;
        }
    }

    public double getPollutionForPoint(double lat, double lon) {
        if (points.isEmpty()) {
            // Si ves esto en la terminal, el JSON no se ha cargado
            logger.info("ALERTA: No hay datos de polución cargados.");
            return 0.0;
        }

        PollutionPoint nearest = null;
        double minDist = Double.MAX_VALUE;

        for (PollutionPoint p : points) {
            double dist = distance(lat, lon, p.lat, p.lon);
            if (dist < minDist) {
                minDist = dist;
                nearest = p;
            }
        }

        // Si la estación más cercana está a más de 10km, quizás mejor devolver 0
        if (nearest != null && minDist < 10.0) {
            return nearest.value;
        }
        return 0.0;
    }

    // 🔹 Midpoint
    public double getPollutionMidpoint(double lat1, double lon1, double lat2, double lon2) {
        double midLat = (lat1 + lat2) / 2;
        double midLon = (lon1 + lon2) / 2;

        return getPollutionForPoint(midLat, midLon);
    }

    // 🔹 Distancia simple
    private double distance(double lat1, double lon1, double lat2, double lon2) {
        double p = 0.017453292519943295; // Math.PI / 180
        double a = 0.5 - Math.cos((lat2 - lat1) * p) / 2 +
                Math.cos(lat1 * p) * Math.cos(lat2 * p) *
                        (1 - Math.cos((lon2 - lon1) * p)) / 2;
        return 12742 * Math.asin(Math.sqrt(a)); // Resultado en KM
    }

}
