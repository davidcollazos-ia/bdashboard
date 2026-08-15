# Pipeline de normalización PID

Este flujo convierte los ficheros fuente del proyecto en capas limpias y reproducibles.

## Objetivo

Partir de los archivos originales y generar, con una sola ejecución del script, los ficheros listos para análisis y visor:

- capas geográficas canónicas y ligeras
- destinos normalizados
- POIs normalizados
- POIs enriquecidos con destino y jerarquía geográfica

Mapa conceptual general:

- [modelo-relacional-pid.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/modelo-relacional-pid.md)

## Entradas

### 1) Capa geográfica

- `geodata/municipios.geojson`
- `geodata/provincias.geojson`
- `geodata/comunidades_autonomas.geojson`

### 2) Destinos

- Excel de destinos principales
- Excel de destinos-gestores

El script no depende del nombre exacto del archivo, sino de su estructura.

### 3) Seguimiento de POIs

- `docs/seguimiento_PRO_20260727.json`

Este archivo contiene:

- `meta`
- `points`

La lista `points` incluye 22.781 registros con:

- `dti`
- `uri`
- `lat`
- `lon`
- `class`
- `name`
- `range2_out`

## Flujo

### Paso 1. Normalización geográfica

El script genera una capa base y una capa ligera por cada nivel:

- municipios
- provincias
- comunidades autónomas
- comarcas como capa de referencia
- propuesta municipio-comarca derivada del audit

### Paso 2. Normalización de destinos

Se crean ficheros limpios con:

- nombre del destino
- nombre normalizado
- gestor
- CIF
- provincia
- comunidad autónoma
- métricas asociadas

El detalle de cada salida de destinos está documentado en:

- [destinos-normalizados-columnas.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/destinos-normalizados-columnas.md)

### Paso 3. Normalización de POIs

Se lee `seguimiento_PRO_20260727.json` y se genera:

- `pois_normalizados.csv`
- `pois_normalizados.geojson`

Cada POI conserva:

- identificador
- clase
- nombre
- `dti`
- `dti_norm`
- coordenadas
- bandera de coordenadas

### Paso 4. Enlace POI -> Destino

El destino se resuelve por:

- `dti_norm`
- `nombre_destino_norm`

La salida incorpora:

- `destino_nombre`
- `destino_nombre_norm`
- `destino_entidad_gestora`
- `destino_cif_entidad_gestora`
- `destino_comunidad_autonoma`
- `destino_provincia`
- `destino_match`

El diccionario completo de columnas del CSV enriquecido está documentado en:

- [pois-enriquecidos-columnas.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/pois-enriquecidos-columnas.md)

### Paso 5. Enlace geográfico

Se hace un cruce espacial con municipios:

- primero `within`
- después, si no hay match, una segunda pasada `nearest` con umbral limitado
- si tampoco encaja, se deja `unmatched`

Estados posibles:

- `matched`
- `nearest`
- `unmatched`

## Salidas

### Geografía

- `normalized/geo/municipios_lite.geojson`
- `normalized/geo/provincias_lite.geojson`
- `normalized/geo/comunidades_autonomas_lite.geojson`

### Destinos

- `normalized/destinos/uso_pid_normalizado.csv`
- `normalized/destinos/modulos_comunes_normalizado.csv`
- `normalized/destinos/datos_turisticos_normalizado.csv`
- `normalized/destinos/datos_no_ontologicos_normalizado.csv`
- `normalized/destinos/destinos_gestores_normalizado.csv`

### POIs

- `normalized/pois/pois_normalizados.csv`
- `normalized/pois/pois_normalizados.geojson`
- `normalized/pois/pois_enriquecidos.csv`
- `normalized/pois/pois_enriquecidos.geojson`

### Auditoría

- `normalized/pois/audit_summary.json`

## Ejecución

```bash
python scripts/normalize_pid_data.py
```

## Principio de diseño

No hay pasos manuales obligatorios. La idea es que el script regenere todo el modelo local desde las fuentes originales, de forma repetible y trazable.
