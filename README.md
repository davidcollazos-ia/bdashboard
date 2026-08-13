# PID Dashboard

Visor interactivo para explorar el JSON de auditoría de PID con mapa, filtros y paneles de resumen.

## Qué hace

- Carga automáticamente `audit_PRO_20260710_164731_enriched.json` si el archivo está junto al `index.html`.
- Permite cargar manualmente cualquier JSON enriquecido desde el navegador.
- Muestra un mapa con recursos geolocalizados o estimados por municipio.
- Filtra por `municipio`, `provincia` y `clase`.
- Separa los recursos sin municipio, provincia ni coordenadas en una tabla de "otros".

## Archivos esperados

- `index.html`
- `audit_PRO_20260710_164731_enriched.json`

## Uso local

1. Abre `index.html` en un navegador.
2. Si el JSON enriquecido está en la misma carpeta, se cargará automáticamente.
3. Si no, usa el selector para abrir el archivo manualmente.

## Notas

- El mapa usa Leaflet.
- Si un recurso no tiene coordenadas, el visor intenta colocarlo en el centro estimado de su municipio.
- Los puntos sin datos geográficos suficientes se muestran en la tabla de "otros".
