# Plan de normalización de campos

Objetivo: reducir peso, evitar duplicidades y conservar solo lo necesario para análisis, joins y visualización.

## Criterio general

- `keep`: campo canónico que merece quedar en la capa limpia.
- `normalize`: campo útil, pero que conviene estandarizar a una clave o formato común.
- `derive`: campo que se puede calcular desde otra tabla o capa.
- `drop`: campo de proceso, redundante o demasiado verboso para la capa limpia.

## 1) `audit_PRO_20260710_164731 (1).json`

### Qué representa

- No es un dataset plano.
- Es un contenedor de fases, inferencias, metadatos y contadores por destino.
- La parte de valor analítico está en las entidades por destino y en sus métricas resumidas.

### Recomendación por bloques

- `env`: `keep` solo si necesitamos trazabilidad de ejecución; si no, `drop`.
- `url`: `keep` como metadato de origen.
- `phases_run`: `drop` si no vamos a auditar el pipeline.
- `timestamp`: `keep` como fecha de extracción.
- `phase1`: `keep` parcial, solo los agregados globales.
- `phase2`: `keep`, pero solo sus contadores por destino.
- `phase3`: `keep`, pero solo el resumen por tipo de entidad/destino.
- `phase4`: `keep` parcialmente, solo campos de procedencia realmente útiles.
- `phase5` a `phase9`: revisar uno a uno; si son trazas de ejecución o inferencia, `drop` en la capa analítica.

### Campos candidatos a conservar en capa limpia

- `total_data`
- `total_inferences`
- `counts.total`
- `counts.event`
- `counts.tourismResource`
- `counts.tourismOrRelatedFacility`
- `counts.tourismOrganisation`
- `counts.tourismService`
- `counts.tourismDestination`
- `counts.publicService`
- `counts.specialOffer`
- `counts.transportInfrastructure`
- `createdBy`
- `updatedBy`
- `lastUpdateDate`
- `version`
- `method`
- `entities_seen`
- `initialObservedDate`
- `provenance_complete`
- `expected_entities`

### Campos a descartar o dejar solo en raw

- listas largas de URIs
- grafos de inferencia completos
- trazas de usuario/correo si no son necesarias para análisis
- `note` de proceso
- mapas de `creatorCounts` y `updaterCounts` completos

## 2) `InfoBeneficiarios_v1.61_20260730.xlsx`

### Hoja `Info General`

- `Unnamed: 0`: `drop`
- `Unnamed: 1`: `keep` como etiqueta/sección
- `Unnamed: 2`: `keep` como descripción
- `Unnamed: 3`: `normalize` a fecha o metadato de extracción

### Hoja `Uso de la PID`

#### Campos a conservar

- `Nombre Destino`
- `Entidad Gestora`
- `CIF Entidad Gestora`
- `Fecha Alta Destino`
- `Estado Destino`
- `Nº de Usuarios`

#### Campos a normalizar

- `Comunidad Autónoma` -> clave `codigo_ccaa`
- `Provincia` -> clave `codigo_provincia`

#### Campos a descartar

- ninguno de entrada, salvo que después detectemos duplicados o columnas vacías

### Hoja `Módulos Comunes`

#### Campos a conservar

- `Nombre Destino`
- `Entidad Gestora`
- `CIF Entidad Gestora`
- `N Usuarios con Acceso`
- `Solución Digital`
- `Fecha de Contratación S.D.` 

#### Campos a normalizar

- `Comunidad Autónoma`
- `Provincia`

#### Campos a descartar

- ninguno de entrada, salvo redundancias posteriores

### Hoja `Datos Turísticos`

#### Campos a conservar

- `NOMBRE_DESTINO`
- `ID_DESTINO`
- `NOMBRE_GRAFO`
- `ID_GRAFO`
- `F_ALTA_GRAFO`

#### Campos a normalizar

- `TRIPLETAS_GRAFO`
- `TRIPLETAS_GRAFO 09/07/2026`
- `TRIPLETAS_GRAFO 27/07/2026`
- `TRIPLETAS_GRAFO 30/07/2026`

#### Campos a descartar

- si se conserva solo el valor más reciente, las columnas históricas pueden pasar a raw

### Hoja `Datos No ontológicos`

#### Campos a conservar

- `Nombre Destino`
- `Entidad Gestora`
- `CIF Entidad Gestora`
- `Fecha Alta`
- `Tipología`
- `Número de registros`

#### Campos a normalizar

- `Contenido` -> extraer solo campos clave y guardar raw aparte si hace falta

#### Campos a descartar

- `Contenido` completo en la capa limpia
- registros de prueba o validación si se identifican

### Hoja `Destinos Gestores`

#### Campos a conservar

- `Nombre Destino Gestor`
- `Entidad Gestora Destino Gestor`
- `CIF Entidad Gestora Destino Gestor`
- `Nombre Destino Gestionado`
- `Entidad Gestora Destino Gestionado`
- `CIF Entidad Gestora Destino Gestionado`
- `Solución Proporcionada por el Gestor`

#### Campos a normalizar

- `Provincia Destino Gestor`
- `CCAA Destino Gestor`

## 3) `InfoBeneficiarios_Gestores_20260730.xlsx`

### Hoja `Destinos Gestores`

#### Campos a conservar

- `Nombre Destino Gestor`
- `Entidad Gestora Destino Gestor`
- `CIF Entidad Gestora Destino Gestor`
- `Nombre Destino Gestionado`
- `Entidad Gestora Destino Gestionado`
- `CIF Entidad Gestora Destino Gestionado`
- `Solución Proporcionada por el Gestor`

#### Campos a normalizar

- `Provincia Destino Gestor`
- `CCAA Destino Gestor`

#### Campos a descartar

- ninguno si queremos conservar la relación gestor-destino

## 4) Regla práctica de recorte

- Si un campo se puede calcular a partir de otro con fiabilidad, no debe vivir en la capa limpia.
- Si un campo solo aporta trazabilidad de ejecución, debe quedar en raw.
- Si un campo está repetido en varias hojas con el mismo significado, hay que canonizarlo una sola vez.
- Si un campo es texto largo semiestructurado, mejor extraer los atributos útiles y dejar el resto fuera de la capa limpia.

## 5) Próximo paso

Construir una capa normalizada mínima con:

- `destinos`
- `pois`
- `equivalencias_geograficas`
- `raw`

Y luego generar vistas ligeras para el visor.
