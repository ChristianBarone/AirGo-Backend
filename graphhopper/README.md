# Instrucciones de uso

Por ahora la ruta se hará con un solo archivo JSON estático.
Después se implementará un script para leer datos automáticamente.

1) El mapa no está cargado:
   1) Descargar: python download_pollution.py
   2) Se generará un archivo osm.pbf
   3) Crear carpeta "osm" en el root (/graphhopper) y guardar el .pbf

2) Compilar: mvn clean install -DskipTests

3) Ejecutar: java -jar web/target/graphhopper-web-12.0-SNAPSHOT.jar server config.yml

4) Ir al servidor y probar motor una vez esté andando (perfil bici): http://localhost:8080/maps/?profile=eco_bike&layer=OpenStreetMap

