# Diccionario de columnas de `pois_enriquecidos.csv`

Este archivo documenta la salida enriquecida de POIs generada por `scripts/normalize_pid_data.py`.

La idea es que esta tabla sea la capa final de consumo para análisis, visor y futuras uniones con otras fuentes.

## Propósito

Cada fila representa un POI normalizado a partir del JSON de seguimiento. Sobre esa base se añade:

- trazabilidad de origen
- resolución de destino
- enriquecimiento geográfico por municipio, provincia y comunidad autónoma
- estado del cruce espacial

## Columnas

### Identidad y trazabilidad

- `phase`: fase de procedencia del registro. En la práctica marca el flujo de origen.
- `entity_key`: clave de entidad usada como identificador técnico.
- `entity_name`: nombre técnico de la entidad fuente.
- `entity_type`: tipo de entidad de origen, por ejemplo `poi_point`.
- `category`: categoría semántica o clase principal del POI.
- `name`: nombre del POI tal como llega en la fuente.
- `class`: clase original del recurso en el JSON.
- `score`: puntuación de confianza o relevancia si venía informada.
- `razon`: motivo o explicación asociada al registro, si existe.

### Coordenadas

- `lat`: latitud normalizada.
- `lon`: longitud normalizada.
- `has_coordinates`: indica si el registro final dispone de coordenadas válidas.
- `coord_source`: origen de la coordenada usada.

Valores esperados:

- `flat_fields`: coordenadas leídas directamente de campos planos del JSON
- `nested_geometry`: coordenadas extraídas de una geometría anidada
- `geocoded`: coordenadas obtenidas por geocodificación

### Trazabilidad del origen PID

- `dti`: identificador de destino turístico asociado al POI en la fuente.
- `dti_norm`: versión normalizada de `dti` para hacer el match.
- `uri`: URI original del recurso.
- `range2_out`: indicador o bandera de salida que venía en el JSON.

### Match de destino

- `destino_nombre`: nombre del destino resuelto.
- `destino_nombre_norm`: nombre del destino normalizado.
- `destino_entidad_gestora`: entidad gestora asociada al destino.
- `destino_cif_entidad_gestora`: CIF de la entidad gestora, si existe.
- `destino_comunidad_autonoma`: comunidad autónoma declarada para el destino.
- `destino_provincia`: provincia declarada para el destino.
- `destino_match`: indica si el POI se ha podido vincular a un destino conocido.

Valores habituales:

- `matched`
- `unmatched`

### Jerarquía geográfica

- `codigo_ine`: código INE del municipio final asignado.
- `nombre_municipio`: nombre del municipio final asignado.
- `codigo_provincia`: código de provincia.
- `nombre_provincia`: nombre de provincia.
- `codigo_ccaa`: código de comunidad autónoma.
- `nombre_ccaa`: nombre de comunidad autónoma.

### Estado del cruce geográfico

- `match_status_geo`: estado del enriquecimiento espacial.

Valores posibles:

- `matched`: el punto cae dentro de un municipio
- `nearest`: no cayó dentro, pero se asignó al municipio más cercano dentro del umbral permitido
- `unmatched`: no se pudo asignar con seguridad

## Lectura recomendada

El flujo completo se explica en:

- [pipeline-normalizacion.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/pipeline-normalizacion.md)

## Nota de uso

Este CSV no pretende ser solo una copia del JSON original. Es la tabla ya lista para:

- análisis
- cruces con destinos
- uso en visor
- control de calidad

Por eso conserva solo los campos útiles para el trabajo operativo y documental.
