# PID Dashboard

Visor interactivo para explorar el seguimiento de PID convertido a GeoJSON.

## Qué hace

- Carga automáticamente `seguimiento_PRO_20260727_123406.geojson` si está junto al `index.html`.
- Permite cargar manualmente un GeoJSON desde el navegador.
- Muestra un mapa con recursos geolocalizados.
- Filtra por `municipio`, `provincia` y `clase`.
- Actualiza los paneles de resumen según filtros y zoom.

## Archivos principales

- `index.html`
- `seguimiento_PRO_20260727_123406.geojson`

## Uso local

1. Sirve la carpeta con un servidor local, por ejemplo `python -m http.server 8000`.
2. Abre `http://localhost:8000/` en el navegador.
3. Si `seguimiento_PRO_20260727_123406.geojson` está en la misma carpeta, se cargará automáticamente.
4. Si no, usa el selector para abrir otro GeoJSON manualmente.

## Nota

- El mapa usa Leaflet y el GeoJSON está preparado para trabajarlo mejor en visores GIS.
