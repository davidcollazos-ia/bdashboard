# PID Dashboard

Visor interactivo para explorar el GeoJSON de auditoría de PID con mapa, filtros y paneles de resumen.

## Qué hace

- Carga automáticamente `audit_PRO_20260710_164731.geojson` si el archivo está junto al `index.html`.
- Permite cargar manualmente un GeoJSON o un JSON enriquecido desde el navegador.
- Muestra un mapa con recursos geolocalizados.
- Filtra por `municipio`, `provincia` y `clase`.
- Separa los recursos sin municipio, provincia ni coordenadas en una tabla de "otros".

## Archivos esperados

- `index.html`
- `audit_PRO_20260710_164731.geojson`

## Uso local

1. Sirve la carpeta con un servidor local, por ejemplo `python -m http.server 8000`.
2. Abre `http://localhost:8000/` en el navegador.
3. Si `audit_PRO_20260710_164731.geojson` está en la misma carpeta, se cargará automáticamente.
4. Si no, usa el selector para abrir el archivo manualmente.

## Importante

- Si abres `index.html` con doble clic, el navegador puede bloquear la carga automática por restricciones de `file://`.
- Para ver la carga real antes de publicar en Pages, usa siempre un servidor local.

## Notas

- El mapa usa Leaflet.
- El GeoJSON concentra la geometría en `geometry` y deja el resto de campos en `properties`.
- Los puntos sin datos geográficos suficientes se muestran en la tabla de "otros".
