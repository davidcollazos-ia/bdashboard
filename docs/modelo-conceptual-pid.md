# Modelo conceptual PID

Este documento resume el criterio base del modelo de datos:

- La capa geográfica canónica es `municipio`.
- `provincia` y `comunidad_autonoma` forman parte de la jerarquía geográfica.
- La unidad semántica de negocio es el `destino_turistico`.
- `comarca`, `diputacion`, `consell` y `comunidad_autonoma` pueden ser destinos turísticos con datos propios.
- No todas las entidades tienen `codigo_ine`, por lo que el modelo necesita claves internas y tablas de equivalencia.

![Modelo conceptual PID](./modelo-conceptual-pid.svg)

## Lectura del diagrama

- `Municipio` es la base para joins y codificación.
- `Destino turístico` es la entidad central donde cuelgan los hechos analíticos.
- `Fuentes de datos` llegan con nombres y deben normalizarse antes de enlazar.
- `Normalización y equivalencias` resuelve nombres a claves canónicas.
- `Entidades especiales` conservan su identidad aunque no tengan código INE.

## Implicación clave

Los análisis pueden agregarse por municipio, provincia o comunidad autónoma, pero el dato de negocio debe conservar el destino turístico original cuando esa sea la unidad de referencia.
