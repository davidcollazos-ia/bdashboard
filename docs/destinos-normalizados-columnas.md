# Diccionario de salidas de destinos normalizados

Este documento describe las tablas que genera el pipeline a partir de los Excel de entrada.

La intención es que los dos ficheros fuente de beneficiarios y gestores se conviertan en una capa limpia, estable y reutilizable.

## Entradas de origen

- `docs/InfoBeneficiarios_v1.61_20260730.xlsx`
- `docs/InfoBeneficiarios_Gestores_20260730.xlsx`

El script detecta los libros por su estructura, no por el nombre exacto.

## Salidas generadas

### 1) `uso_pid_normalizado.csv`

Resumen de la adopción o uso de la PID por destino.

Columnas:

- `nombre_destino`: nombre original del destino
- `nombre_destino_norm`: nombre normalizado para cruces
- `entidad_gestora`: entidad que gestiona el destino
- `entidad_gestora_norm`: entidad gestora normalizada
- `cif_entidad_gestora`: CIF de la entidad gestora
- `fecha_alta_destino`: fecha de alta del destino
- `estado_destino`: estado operativo o de activación
- `comunidad_autonoma`: nombre de la CCAA
- `codigo_ccaa`: código de la CCAA
- `provincia`: nombre de la provincia
- `codigo_provincia`: código de la provincia
- `numero_usuarios`: número de usuarios asociados

Uso principal:

- cruce por `nombre_destino_norm`
- control de cobertura territorial
- identificación de gestores y destino operativo

### 2) `modulos_comunes_normalizado.csv`

Resumen de módulos comunes y adopción de solución digital.

Columnas:

- `nombre_destino`: nombre original del destino
- `nombre_destino_norm`: nombre normalizado para cruces
- `entidad_gestora`: entidad que gestiona el destino
- `entidad_gestora_norm`: entidad gestora normalizada
- `cif_entidad_gestora`: CIF de la entidad gestora
- `comunidad_autonoma`: nombre de la CCAA
- `codigo_ccaa`: código de la CCAA
- `provincia`: nombre de la provincia
- `codigo_provincia`: código de la provincia
- `numero_usuarios_acceso`: número de usuarios con acceso
- `solucion_digital`: solución digital asociada
- `fecha_contratacion_sd`: fecha de contratación de la solución digital

Uso principal:

- análisis de implantación tecnológica
- cruces por destino y gestor
- control de fecha de contratación y volumen de acceso

### 3) `datos_turisticos_normalizado.csv`

Resumen de datos turísticos y metadatos de grafo.

Columnas:

- `nombre_destino`: nombre original del destino
- `nombre_destino_norm`: nombre normalizado para cruces
- `id_destino`: identificador del destino
- `nombre_grafo`: nombre del grafo
- `id_grafo`: identificador del grafo
- `fecha_alta_grafo`: fecha de alta del grafo
- `tripletas_grafo`: número de tripletas del grafo
- `tripletas_20260709`: estado o conteo histórico a fecha 09/07/2026
- `tripletas_20260727`: estado o conteo histórico a fecha 27/07/2026
- `tripletas_20260730`: estado o conteo histórico a fecha 30/07/2026

Uso principal:

- seguimiento del estado semántico del destino
- control de evolución del grafo
- enlace con el universo de destino normalizado

### 4) `datos_no_ontologicos_normalizado.csv`

Resumen de datos no ontológicos o textuales asociados al destino.

Columnas:

- `nombre_destino`: nombre original del destino
- `nombre_destino_norm`: nombre normalizado para cruces
- `entidad_gestora`: entidad gestora
- `cif_entidad_gestora`: CIF de la entidad gestora
- `fecha_alta`: fecha de alta
- `tipologia`: tipología del dato
- `contenido_resumen`: resumen extraído del contenido original
- `numero_registros`: número de registros o elementos asociados

Uso principal:

- conservar solo lo esencial de contenido libre
- análisis cualitativo
- enlace con destino normalizado

### 5) `destinos_gestores_normalizado.csv`

Relación entre destino gestor y destino gestionado.

Columnas:

- `nombre_destino_gestor`: destino que actúa como gestor
- `nombre_destino_gestor_norm`: versión normalizada del gestor
- `entidad_gestora_destino_gestor`: entidad gestora del destino gestor
- `cif_entidad_gestora_destino_gestor`: CIF del gestor
- `provincia_destino_gestor`: provincia del destino gestor
- `ccaa_destino_gestor`: comunidad autónoma del destino gestor
- `nombre_destino_gestionado`: destino gestionado
- `nombre_destino_gestionado_norm`: versión normalizada del destino gestionado
- `entidad_gestora_destino_gestionado`: entidad gestora del destino gestionado
- `cif_entidad_gestora_destino_gestionado`: CIF del destino gestionado
- `solucion_proporcionada`: solución o relación aportada por el gestor

Uso principal:

- modelar relaciones entre destinos
- identificar dependencias de gestión
- consolidar contexto de la red PID

## Cómo se usan después

Estos CSV son la base para:

- hacer match con `dti` desde los POIs
- enriquecer por municipio, provincia y CCAA
- construir vistas para análisis y visor

## Regla de lectura

En la capa limpia, el nombre humano se conserva, pero el cruce debe hacerse siempre con:

- `nombre_destino_norm`
- `dti_norm`
- códigos geográficos cuando existan

