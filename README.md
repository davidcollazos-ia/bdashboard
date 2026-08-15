# PID Dashboard

Visor interactivo y pipeline documental para el seguimiento de PID.

## Qué hace

- Carga automáticamente el seguimiento convertido a GeoJSON.
- Permite explorar POIs, destinos y jerarquía geográfica.
- Genera capas normalizadas y enriquecidas desde las fuentes originales.
- Automatiza el match entre `dti`, destino y municipio.

## Flujo automatizado

El pipeline principal está documentado en:

- [docs/pipeline-normalizacion.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/pipeline-normalizacion.md)

Resumen:

- lee el JSON de seguimiento
- normaliza destinos
- cruza POIs con destinos
- resuelve jerarquía municipal, provincial y autonómica
- genera capa comarcal y propuesta municipio-comarca
- deja salidas reproducibles en `normalized/`

Documentación de salida:

- [docs/pois-enriquecidos-columnas.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/pois-enriquecidos-columnas.md)
- [docs/destinos-normalizados-columnas.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/destinos-normalizados-columnas.md)
- [docs/modelo-relacional-pid.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/modelo-relacional-pid.md)
- [docs/inventario-final-salidas.md](C:/Users/dcollazos.SEGITTUR/Documents/ChatGPT/bdashboard/docs/inventario-final-salidas.md)

## Archivos principales

- `index.html`
- `scripts/normalize_pid_data.py`
- `docs/seguimiento_PRO_20260727.json`
- `normalized/pois/pois_enriquecidos.geojson`

## Uso local

1. Sirve la carpeta con un servidor local, por ejemplo `python -m http.server 8000`.
2. Abre `http://localhost:8000/` en el navegador.
3. Ejecuta `python scripts/normalize_pid_data.py` para regenerar los datos.

## Nota

- La fuente de POIs real es `docs/seguimiento_PRO_20260727.json`.
- El script deja controlados los estados `matched`, `nearest` y `unmatched`.
