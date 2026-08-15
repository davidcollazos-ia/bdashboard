# Inventario final de salidas

Este documento resume las tablas y capas que deja el pipeline después de la última normalización.

## Capas geográficas

- `normalized/geo/municipios_lite.csv`
- `normalized/geo/municipios_lite.geojson`
- `normalized/geo/provincias_lite.csv`
- `normalized/geo/provincias_lite.geojson`
- `normalized/geo/comunidades_autonomas_lite.csv`
- `normalized/geo/comunidades_autonomas_lite.geojson`
- `normalized/geo/comarcas_lite.csv`
- `normalized/geo/municipio_comarca_propuesta.csv`
- `normalized/geo/comarcas_propuesta.csv`

## Destinos

- `normalized/destinos/uso_pid_normalizado.csv`
- `normalized/destinos/modulos_comunes_normalizado.csv`
- `normalized/destinos/datos_turisticos_normalizado.csv`
- `normalized/destinos/datos_no_ontologicos_normalizado.csv`
- `normalized/destinos/destinos_gestores_normalizado.csv`

## POIs

- `normalized/pois/pois_normalizados.csv`
- `normalized/pois/pois_normalizados.geojson`
- `normalized/pois/pois_enriquecidos.csv`
- `normalized/pois/pois_enriquecidos.geojson`
- `normalized/pois/audit_summary.json`

## Archivos de apoyo

- `normalized/manifest.json`
- `docs/PID_dashboard_documentacion.docx`

## Lectura rápida

- `municipios_lite` es la base territorial mínima.
- `provincias_lite` y `comunidades_autonomas_lite` son las capas superiores.
- `comarcas_lite` inventaría las entidades comarcales detectadas.
- `municipio_comarca_propuesta` es la relación inferida municipio-comarca.
- `comarcas_propuesta` resume la propuesta a nivel de comarca.

