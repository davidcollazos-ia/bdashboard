from __future__ import annotations

import json
import re
import unicodedata
import time
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GEODATA = ROOT / "geodata"
OUTPUT = ROOT / "normalized"
ENABLE_GEOCODING = True
GEOCODER_USER_AGENT = "bdashboard-pid-normalizer"
GEOCODER_MIN_DELAY_SECONDS = 1.0
SEGUIMIENTO_JSON = DOCS / "seguimiento_PRO_20260727.json"


def ensure_output_dirs() -> None:
    for path in [OUTPUT, OUTPUT / "geo", OUTPUT / "destinos", OUTPUT / "pois", OUTPUT / "raw"]:
        path.mkdir(parents=True, exist_ok=True)


def find_single_file(patterns: list[str], must_contain: list[str] | None = None, must_not_contain: list[str] | None = None) -> Path:
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(DOCS.glob(pattern))
    filtered: list[Path] = []
    for candidate in candidates:
        name = candidate.name.lower()
        if must_contain and not all(token in name for token in must_contain):
            continue
        if must_not_contain and any(token in name for token in must_not_contain):
            continue
        filtered.append(candidate)

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in filtered:
        if candidate not in seen:
            unique.append(candidate)
            seen.add(candidate)

    if not unique:
        raise FileNotFoundError(f"No se encontro ningun archivo que encaje con {patterns}")
    if len(unique) > 1:
        raise FileNotFoundError(f"Se encontraron varios archivos para {patterns}: {[p.name for p in unique]}")
    return unique[0]


def strip_accents(text: Any) -> str:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    text = str(text).strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalize_text(text: Any) -> str:
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def canonical_sheet_name(sheet_names: list[str], wanted: str) -> str:
    wanted_norm = normalize_text(wanted)
    for name in sheet_names:
        if normalize_text(name) == wanted_norm:
            return name
    for name in sheet_names:
        if wanted_norm in normalize_text(name):
            return name
    raise KeyError(f"No se encontro una hoja compatible con {wanted}: {sheet_names}")


def pick_col(df: pd.DataFrame, wanted: str) -> str:
    wanted_norm = normalize_text(wanted)
    for col in df.columns:
        col_norm = normalize_text(col)
        if col_norm == wanted_norm or wanted_norm in col_norm:
            return col
    raise KeyError(f"No se encontro una columna compatible con {wanted}. Columnas: {list(df.columns)}")


def as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        return int(value)
    text = str(value).strip()
    text = text.replace(".", "").replace(" ", "")
    text = text.replace(",", ".")
    try:
        return int(float(text))
    except ValueError:
        return None


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        return float(value)
    text = str(value).strip().replace(" ", "")
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def extract_coordinates(payload: Any) -> dict[str, Any]:
    result = {
        "latitude": None,
        "longitude": None,
        "coord_source": None,
        "has_coordinates": False,
    }

    def assign(lat: Any, lon: Any, source: str) -> None:
        lat_f = as_float(lat)
        lon_f = as_float(lon)
        if lat_f is None or lon_f is None:
            return
        result["latitude"] = lat_f
        result["longitude"] = lon_f
        result["coord_source"] = source
        result["has_coordinates"] = True

    if isinstance(payload, dict):
        for lat_key, lon_key, source in [
            ("lat", "lon", "flat_fields"),
            ("latitude", "longitude", "flat_fields"),
            ("Latitude", "Longitude", "flat_fields"),
        ]:
            if lat_key in payload and lon_key in payload:
                assign(payload.get(lat_key), payload.get(lon_key), source)
                if result["has_coordinates"]:
                    return result

        for key in ["location", "hasLocation", "gps", "geometry"]:
            value = payload.get(key)
            if isinstance(value, dict):
                inner = value.get("value") if isinstance(value.get("value"), dict) else value
                if isinstance(inner, dict):
                    coords = inner.get("coordinates")
                    if isinstance(coords, list) and len(coords) >= 2:
                        lon, lat = coords[0], coords[1]
                        assign(lat, lon, f"{key}.coordinates")
                        if result["has_coordinates"]:
                            return result
                    for lat_key, lon_key in [("lat", "long"), ("lat", "lon"), ("latitude", "longitude")]:
                        if lat_key in inner and lon_key in inner:
                            assign(inner.get(lat_key), inner.get(lon_key), f"{key}.{lat_key}_{lon_key}")
                            if result["has_coordinates"]:
                                return result

        for key, value in payload.items():
            if isinstance(value, dict):
                inner = value.get("value") if isinstance(value.get("value"), dict) else value
                if isinstance(inner, dict):
                    coords = inner.get("coordinates")
                    if isinstance(coords, list) and len(coords) >= 2:
                        lon, lat = coords[0], coords[1]
                        assign(lat, lon, f"{key}.coordinates")
                        if result["has_coordinates"]:
                            return result

    return result


def build_address_candidates(record: dict[str, Any]) -> list[str]:
    parts = [
        record.get("streetAddress"),
        record.get("address"),
        record.get("locality"),
        record.get("municipality"),
        record.get("province"),
        record.get("autonomousCommunity"),
        record.get("postalCode"),
    ]
    clean = [strip_accents(p) for p in parts if strip_accents(p)]
    if len(clean) < 2:
        return []
    return [", ".join(clean + ["España"])]


def geocode_address(query: str, geocoder: Any, pause_seconds: float = 1.0) -> dict[str, Any]:
    try:
        location = geocoder(query)
    except Exception:
        location = None
    if not location:
        return {"latitude": None, "longitude": None, "geocoded": False, "geocode_query": query}
    return {
        "latitude": getattr(location, "latitude", None),
        "longitude": getattr(location, "longitude", None),
        "geocoded": True,
        "geocode_query": query,
        "geocode_display_name": getattr(location, "address", None),
    }


def load_geography() -> dict[str, pd.DataFrame]:
    return {
        "municipios": gpd.read_file(GEODATA / "municipios.geojson"),
        "provincias": gpd.read_file(GEODATA / "provincias.geojson"),
        "comunidades_autonomas": gpd.read_file(GEODATA / "comunidades_autonomas.geojson"),
    }


def write_lookup_tables(geoms: dict[str, pd.DataFrame]) -> None:
    lookup_dir = OUTPUT / "geo"

    municipios = geoms["municipios"][["codigo_ine", "nombre_municipio", "codigo_provincia", "codigo_ccaa", "geometry"]].copy()
    municipios["municipio_norm"] = municipios["nombre_municipio"].map(normalize_text)
    municipios["id_comarca"] = None
    municipios["nombre_municipio"] = municipios["nombre_municipio"].map(strip_accents)
    municipios.to_file(lookup_dir / "municipios_lite.geojson", driver="GeoJSON")
    municipios.drop(columns="geometry").to_csv(lookup_dir / "municipios_lite.csv", index=False)

    provincias = geoms["provincias"][["codigo_provincia", "nombre_provincia", "codigo_ccaa", "geometry"]].copy()
    provincias["provincia_norm"] = provincias["nombre_provincia"].map(normalize_text)
    provincias["nombre_provincia"] = provincias["nombre_provincia"].map(strip_accents)
    provincias.to_file(lookup_dir / "provincias_lite.geojson", driver="GeoJSON")
    provincias.drop(columns="geometry").to_csv(lookup_dir / "provincias_lite.csv", index=False)

    ccaa = geoms["comunidades_autonomas"][["codigo_ccaa", "nombre_ccaa", "geometry"]].copy()
    ccaa["ccaa_norm"] = ccaa["nombre_ccaa"].map(normalize_text)
    ccaa["nombre_ccaa"] = ccaa["nombre_ccaa"].map(strip_accents)
    ccaa.to_file(lookup_dir / "comunidades_autonomas_lite.geojson", driver="GeoJSON")
    ccaa.drop(columns="geometry").to_csv(lookup_dir / "comunidades_autonomas_lite.csv", index=False)


def build_comarca_reference(destinos: pd.DataFrame, gestores: pd.DataFrame) -> pd.DataFrame:
    def collect(df: pd.DataFrame, name_col: str, province_col: str | None = None, ccaa_col: str | None = None) -> pd.DataFrame:
        if name_col not in df.columns:
            return pd.DataFrame()
        mask = df[name_col].fillna("").astype(str).str.lower().str.contains(
            "comarca|consell|consejo comarcal|mancomunidad de la comarca", regex=True
        )
        subset = df.loc[mask].copy()
        if subset.empty:
            return pd.DataFrame()
        out = pd.DataFrame({
            "nombre_comarca": subset[name_col].map(strip_accents),
            "nombre_comarca_norm": subset[name_col].map(normalize_text),
            "tipo_referencia": subset[name_col].astype(str).map(
                lambda x: "comarca"
                if "comarca" in x.lower() and "consell" not in x.lower() and "consejo comarcal" not in x.lower()
                else ("consell" if "consell" in x.lower() else ("consejo_comarcal" if "consejo comarcal" in x.lower() else "mancomunidad"))
            ),
            "provincia_referencia": subset[province_col].map(strip_accents) if province_col and province_col in subset.columns else None,
            "ccaa_referencia": subset[ccaa_col].map(strip_accents) if ccaa_col and ccaa_col in subset.columns else None,
            "origen_tabla": "destinos_normalizados",
        })
        return out

    frames = [
        collect(destinos, "nombre_destino"),
        collect(gestores, "nombre_destino_gestor", "provincia_destino_gestor", "ccaa_destino_gestor"),
        collect(gestores, "nombre_destino_gestionado", "provincia_destino_gestor", "ccaa_destino_gestor"),
    ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=[
            "id_comarca",
            "nombre_comarca",
            "nombre_comarca_norm",
            "tipo_referencia",
            "provincia_referencia",
            "ccaa_referencia",
            "origen_tabla",
        ])
    ref = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["nombre_comarca_norm", "tipo_referencia"])
    ref.insert(0, "id_comarca", ref["nombre_comarca_norm"])
    return ref[[
        "id_comarca",
        "nombre_comarca",
        "nombre_comarca_norm",
        "tipo_referencia",
        "provincia_referencia",
        "ccaa_referencia",
        "origen_tabla",
    ]]


def build_municipio_comarca_propuesta(audit_path: Path, municipios_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with audit_path.open("r", encoding="utf-8") as f:
        audit = json.load(f)
    municipios = pd.read_csv(municipios_path)
    municipio_names = municipios["nombre_municipio"].dropna().astype(str).tolist()

    stop = {
        "Una", "Valor", "Caso", "Oliva", "Muros", "Les", "Seva", "Luna", "Buena", "Vecinos", "Calles",
        "Antigua", "Frontera", "Peque", "Alto", "Bajo", "Campo", "Campos", "Rio", "Ria", "San", "Santa",
        "Villa", "Villas",
    }
    muni_pool = [m for m in municipio_names if len(m) >= 4 and m not in stop]

    rows: list[dict[str, Any]] = []
    phase6 = audit.get("phase6", {})
    if isinstance(phase6, dict):
        for comarca, payload in phase6.items():
            entities = payload.get("entities", []) if isinstance(payload, dict) else []
            text = " ".join(((e.get("text") or "") + " " + (e.get("name") or "")) for e in entities).lower()
            found: list[tuple[str, int]] = []
            for m in muni_pool:
                count = text.count(m.lower())
                if count:
                    found.append((m, count))
            found.sort(key=lambda x: (-x[1], len(x[0])))
            found = found[:8]
            if not found:
                continue
            total = sum(c for _, c in found)
            for rank, (m, count) in enumerate(found, start=1):
                rows.append({
                    "id_comarca": comarca,
                    "nombre_comarca": comarca.replace("-", " ").title(),
                    "nombre_municipio": m,
                    "peso_mencion": count,
                    "rank_en_comarca": rank,
                    "confianza": round(count / total, 3) if total else 0,
                    "estado": "propuesto",
                    "fuente": "audit_PRO_20260710_164731_text_match",
                })

    detalle = pd.DataFrame(rows).drop_duplicates(["id_comarca", "nombre_municipio"])
    resumen = pd.DataFrame(columns=["id_comarca", "nombre_comarca", "municipios_propuestos", "peso_total", "estado"])
    if not detalle.empty:
        resumen = (
            detalle.groupby(["id_comarca", "nombre_comarca"], as_index=False)
            .agg(municipios_propuestos=("nombre_municipio", "count"), peso_total=("peso_mencion", "sum"))
        )
        resumen["estado"] = "propuesto"
    return detalle, resumen


def read_destinos_workbook() -> Path:
    return find_single_file(["*.xlsx"], must_contain=["beneficiarios"], must_not_contain=["gestor"])


def read_gestores_workbook() -> Path:
    return find_single_file(["*.xlsx"], must_contain=["gestores"])


def load_destino_lookup() -> pd.DataFrame:
    path = OUTPUT / "destinos" / "uso_pid_normalizado.csv"
    if not path.exists():
        return pd.DataFrame(columns=["nombre_destino_norm", "nombre_destino", "entidad_gestora", "cif_entidad_gestora", "comunidad_autonoma", "provincia"])
    df = pd.read_csv(path)
    if "nombre_destino_norm" not in df.columns and "nombre_destino" in df.columns:
        df["nombre_destino_norm"] = df["nombre_destino"].map(normalize_text)
    return df


def normalize_destinos_general() -> pd.DataFrame:
    workbook = read_destinos_workbook()
    sheet = canonical_sheet_name(pd.ExcelFile(workbook).sheet_names, "Uso de la PID")
    df = pd.read_excel(workbook, sheet_name=sheet)
    df = df.rename(columns={
        pick_col(df, "Nombre Destino"): "nombre_destino",
        pick_col(df, "Entidad Gestora"): "entidad_gestora",
        pick_col(df, "CIF Entidad Gestora"): "cif_entidad_gestora",
        pick_col(df, "Fecha Alta Destino"): "fecha_alta_destino",
        pick_col(df, "Estado Destino"): "estado_destino",
        pick_col(df, "Comunidad Autónoma"): "comunidad_autonoma",
        pick_col(df, "Provincia"): "provincia",
        pick_col(df, "Número de Usuarios"): "numero_usuarios",
    })
    df["nombre_destino_norm"] = df["nombre_destino"].map(normalize_text)
    df["entidad_gestora_norm"] = df["entidad_gestora"].map(normalize_text)
    df["cif_entidad_gestora"] = df["cif_entidad_gestora"].map(strip_accents)
    df["comunidad_autonoma"] = df["comunidad_autonoma"].map(strip_accents)
    df["provincia"] = df["provincia"].map(strip_accents)
    df["codigo_ccaa"] = None
    df["codigo_provincia"] = None
    df["numero_usuarios"] = df["numero_usuarios"].map(as_int)
    return df[[
        "nombre_destino",
        "nombre_destino_norm",
        "entidad_gestora",
        "entidad_gestora_norm",
        "cif_entidad_gestora",
        "fecha_alta_destino",
        "estado_destino",
        "comunidad_autonoma",
        "codigo_ccaa",
        "provincia",
        "codigo_provincia",
        "numero_usuarios",
    ]]


def normalize_modulos_comunes() -> pd.DataFrame:
    workbook = read_destinos_workbook()
    sheet = canonical_sheet_name(pd.ExcelFile(workbook).sheet_names, "Módulos Comunes")
    df = pd.read_excel(workbook, sheet_name=sheet)
    df = df.rename(columns={
        pick_col(df, "Nombre Destino"): "nombre_destino",
        pick_col(df, "Entidad Gestora"): "entidad_gestora",
        pick_col(df, "CIF Entidad Gestora"): "cif_entidad_gestora",
        pick_col(df, "Comunidad Autónoma"): "comunidad_autonoma",
        pick_col(df, "Provincia"): "provincia",
        pick_col(df, "N Usuarios con Acceso"): "numero_usuarios_acceso",
        pick_col(df, "Solución Digital"): "solucion_digital",
        pick_col(df, "Fecha de Contratación S.D."): "fecha_contratacion_sd",
    })
    for col in ["nombre_destino", "entidad_gestora", "cif_entidad_gestora", "comunidad_autonoma", "provincia", "solucion_digital"]:
        df[col] = df[col].map(strip_accents)
    df["nombre_destino_norm"] = df["nombre_destino"].map(normalize_text)
    df["entidad_gestora_norm"] = df["entidad_gestora"].map(normalize_text)
    df["numero_usuarios_acceso"] = df["numero_usuarios_acceso"].map(as_int)
    df["codigo_ccaa"] = None
    df["codigo_provincia"] = None
    return df[[
        "nombre_destino",
        "nombre_destino_norm",
        "entidad_gestora",
        "entidad_gestora_norm",
        "cif_entidad_gestora",
        "comunidad_autonoma",
        "codigo_ccaa",
        "provincia",
        "codigo_provincia",
        "numero_usuarios_acceso",
        "solucion_digital",
        "fecha_contratacion_sd",
    ]]


def normalize_datos_turisticos() -> pd.DataFrame:
    workbook = read_destinos_workbook()
    sheet = canonical_sheet_name(pd.ExcelFile(workbook).sheet_names, "Datos Turísticos")
    df = pd.read_excel(workbook, sheet_name=sheet)
    df = df.rename(columns={
        pick_col(df, "NOMBRE_DESTINO"): "nombre_destino",
        pick_col(df, "ID_DESTINO"): "id_destino",
        pick_col(df, "NOMBRE_GRAFO"): "nombre_grafo",
        pick_col(df, "ID_GRAFO"): "id_grafo",
        pick_col(df, "F_ALTA_GRAFO"): "fecha_alta_grafo",
        pick_col(df, "TRIPLETAS_GRAFO"): "tripletas_grafo",
        pick_col(df, "TRIPLETAS_GRAFO 09/07/2026"): "tripletas_20260709",
        pick_col(df, "TRIPLETAS_GRAFO 27/07/2026"): "tripletas_20260727",
        pick_col(df, "TRIPLETAS_GRAFO 30/07/2026"): "tripletas_20260730",
    })
    for col in ["nombre_destino", "id_destino", "nombre_grafo", "id_grafo", "tripletas_grafo", "tripletas_20260709", "tripletas_20260727", "tripletas_20260730"]:
        df[col] = df[col].map(strip_accents)
    df["nombre_destino_norm"] = df["nombre_destino"].map(normalize_text)
    for col in ["tripletas_grafo", "tripletas_20260709", "tripletas_20260727", "tripletas_20260730"]:
        df[col] = df[col].map(as_int)
    return df[[
        "nombre_destino",
        "nombre_destino_norm",
        "id_destino",
        "nombre_grafo",
        "id_grafo",
        "fecha_alta_grafo",
        "tripletas_grafo",
        "tripletas_20260709",
        "tripletas_20260727",
        "tripletas_20260730",
    ]]


def normalize_datos_no_ontologicos() -> pd.DataFrame:
    workbook = read_destinos_workbook()
    sheet = canonical_sheet_name(pd.ExcelFile(workbook).sheet_names, "Datos No ontológicos")
    df = pd.read_excel(workbook, sheet_name=sheet)
    df = df.rename(columns={
        pick_col(df, "Nombre Destino"): "nombre_destino",
        pick_col(df, "Entidad Gestora"): "entidad_gestora",
        pick_col(df, "CIF Entidad Gestora"): "cif_entidad_gestora",
        pick_col(df, "Fecha Alta"): "fecha_alta",
        pick_col(df, "Tipología"): "tipologia",
        pick_col(df, "Contenido"): "contenido",
        pick_col(df, "Número de registros"): "numero_registros",
    })
    for col in ["nombre_destino", "entidad_gestora", "cif_entidad_gestora", "tipologia"]:
        df[col] = df[col].map(strip_accents)
    df["nombre_destino_norm"] = df["nombre_destino"].map(normalize_text)
    df["numero_registros"] = df["numero_registros"].map(as_int)
    df["contenido_resumen"] = df["contenido"].map(lambda x: strip_accents(x)[:1000] if pd.notna(x) else "")
    return df[[
        "nombre_destino",
        "nombre_destino_norm",
        "entidad_gestora",
        "cif_entidad_gestora",
        "fecha_alta",
        "tipologia",
        "contenido_resumen",
        "numero_registros",
    ]]


def normalize_destinos_gestores() -> pd.DataFrame:
    workbook = read_gestores_workbook()
    sheet = canonical_sheet_name(pd.ExcelFile(workbook).sheet_names, "Destinos Gestores")
    df = pd.read_excel(workbook, sheet_name=sheet)
    df = df.rename(columns={
        pick_col(df, "Nombre Destino Gestor"): "nombre_destino_gestor",
        pick_col(df, "Entidad Gestora Destino Gestor"): "entidad_gestora_destino_gestor",
        pick_col(df, "CIF Entidad Gestora Destino Gestor"): "cif_entidad_gestora_destino_gestor",
        pick_col(df, "Provincia Destino Gestor"): "provincia_destino_gestor",
        pick_col(df, "CCAA Destino Gestor"): "ccaa_destino_gestor",
        pick_col(df, "Nombre Destino Gestionado"): "nombre_destino_gestionado",
        pick_col(df, "Entidad Gestora Destino Gestionado"): "entidad_gestora_destino_gestionado",
        pick_col(df, "CIF Entidad Gestora Destino Gestionado"): "cif_entidad_gestora_destino_gestionado",
        pick_col(df, "Solución Proporcionada por el Gestor"): "solucion_proporcionada",
    })
    for col in [
        "nombre_destino_gestor",
        "entidad_gestora_destino_gestor",
        "cif_entidad_gestora_destino_gestor",
        "provincia_destino_gestor",
        "ccaa_destino_gestor",
        "nombre_destino_gestionado",
        "entidad_gestora_destino_gestionado",
        "cif_entidad_gestora_destino_gestionado",
        "solucion_proporcionada",
    ]:
        df[col] = df[col].map(strip_accents)
    df["nombre_destino_gestor_norm"] = df["nombre_destino_gestor"].map(normalize_text)
    df["nombre_destino_gestionado_norm"] = df["nombre_destino_gestionado"].map(normalize_text)
    return df[[
        "nombre_destino_gestor",
        "nombre_destino_gestor_norm",
        "entidad_gestora_destino_gestor",
        "cif_entidad_gestora_destino_gestor",
        "provincia_destino_gestor",
        "ccaa_destino_gestor",
        "nombre_destino_gestionado",
        "nombre_destino_gestionado_norm",
        "entidad_gestora_destino_gestionado",
        "cif_entidad_gestora_destino_gestionado",
        "solucion_proporcionada",
    ]]


def summarize_audit_json() -> dict[str, Any]:
    audit_json = find_single_file(["*.json"], must_contain=["audit", "pro"], must_not_contain=["summary"])
    with audit_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    summary: dict[str, Any] = {
        "url": data.get("url"),
        "timestamp": data.get("timestamp"),
        "phases_run": data.get("phases_run", []),
        "phase1": data.get("phase1", {}),
    }

    for phase_name in ["phase2", "phase3", "phase4", "phase5", "phase6", "phase7", "phase8", "phase9"]:
        phase = data.get(phase_name, {})
        phase_summary: dict[str, Any] = {
            "entity_count": len(phase) if isinstance(phase, dict) else 0,
            "entities": {},
        }
        if isinstance(phase, dict):
            for key, value in phase.items():
                if isinstance(value, dict):
                    phase_summary["entities"][key] = {"keys": list(value.keys())[:50]}
                    if phase_name == "phase4":
                        phase_summary["entities"][key].update({
                            "createdBy": value.get("createdBy"),
                            "updatedBy": value.get("updatedBy"),
                            "lastUpdateDate": value.get("lastUpdateDate"),
                            "version": value.get("version"),
                            "method": value.get("method"),
                            "entities_seen": value.get("entities_seen"),
                            "initialObservedDate": value.get("initialObservedDate"),
                            "provenance_complete": value.get("provenance_complete"),
                            "expected_entities": value.get("expected_entities"),
                        })
                    elif phase_name == "phase2":
                        phase_summary["entities"][key].update({
                            "counts": value.get("counts", {}),
                            "completeness": value.get("completeness", {}),
                            "subcounts": value.get("subcounts", {}),
                        })
                    elif phase_name == "phase3":
                        phase_summary["entities"][key].update({"types": value.get("types", {})})
        summary[phase_name] = phase_summary

    return summary


def normalize_poi_summary() -> pd.DataFrame:
    audit_json = find_single_file(["*.json"], must_contain=["audit", "pro"], must_not_contain=["summary"])
    with audit_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows: list[dict[str, Any]] = []

    phase2 = data.get("phase2", {})
    if isinstance(phase2, dict):
        for destination, payload in phase2.items():
            if not isinstance(payload, dict):
                continue
            counts = payload.get("counts", {}) or {}
            coords = extract_coordinates(payload)
            row: dict[str, Any] = {
                "phase": "phase2",
                "entity_key": destination,
                "entity_name": destination,
                "entity_type": "destination_summary",
                "total": as_int(counts.get("total")),
                "event": as_int(counts.get("event")),
                "tourismResource": as_int(counts.get("tourismResource")),
                "tourismOrRelatedFacility": as_int(counts.get("tourismOrRelatedFacility")),
                "tourismOrganisation": as_int(counts.get("tourismOrganisation")),
                "tourismService": as_int(counts.get("tourismService")),
                "tourismDestination": as_int(counts.get("tourismDestination")),
                "publicService": as_int(counts.get("publicService")),
                "specialOffer": as_int(counts.get("specialOffer")),
                "transportInfrastructure": as_int(counts.get("transportInfrastructure")),
                "otras": as_int(counts.get("otras")),
                "completeness": json.dumps(payload.get("completeness", {}), ensure_ascii=False),
                "subcounts": json.dumps(payload.get("subcounts", {}), ensure_ascii=False),
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "coord_source": coords["coord_source"],
                "has_coordinates": coords["has_coordinates"],
            }
            rows.append(row)

    phase3 = data.get("phase3", {})
    if isinstance(phase3, dict):
        for destination, payload in phase3.items():
            if not isinstance(payload, dict):
                continue
            coords = extract_coordinates(payload)
            types = payload.get("types", {}) or {}
            row = {
                "phase": "phase3",
                "entity_key": destination,
                "entity_name": destination,
                "entity_type": "grouped_destination",
                "types_count": len(types),
                "types": json.dumps(types, ensure_ascii=False),
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "coord_source": coords["coord_source"],
                "has_coordinates": coords["has_coordinates"],
            }
            rows.append(row)

    phase4 = data.get("phase4", {})
    if isinstance(phase4, dict):
        for destination, payload in phase4.items():
            if not isinstance(payload, dict):
                continue
            coords = extract_coordinates(payload)
            row = {
                "phase": "phase4",
                "entity_key": destination,
                "entity_name": destination,
                "entity_type": "provenance_summary",
                "createdBy": strip_accents(payload.get("createdBy")),
                "updatedBy": strip_accents(payload.get("updatedBy")),
                "lastUpdateDate": payload.get("lastUpdateDate"),
                "version": payload.get("version"),
                "method": payload.get("method"),
                "entities_seen": as_int(payload.get("entities_seen")),
                "initialCreatedBy": strip_accents(payload.get("initialCreatedBy")),
                "initialObservedDate": payload.get("initialObservedDate"),
                "latestUpdatedBy": strip_accents(payload.get("latestUpdatedBy")),
                "latestUpdateDate": payload.get("latestUpdateDate"),
                "dominantCreatedBy": strip_accents(payload.get("dominantCreatedBy")),
                "dominantUpdatedBy": strip_accents(payload.get("dominantUpdatedBy")),
                "creatorCounts": json.dumps(payload.get("creatorCounts", {}), ensure_ascii=False),
                "updaterCounts": json.dumps(payload.get("updaterCounts", {}), ensure_ascii=False),
                "note": strip_accents(payload.get("note")),
                "provenance_complete": bool(payload.get("provenance_complete")),
                "expected_entities": as_int(payload.get("expected_entities")),
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "coord_source": coords["coord_source"],
                "has_coordinates": coords["has_coordinates"],
            }
            rows.append(row)

    return pd.DataFrame(rows)


def normalize_json_pois_details() -> pd.DataFrame:
    with SEGUIMIENTO_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows: list[dict[str, Any]] = []
    destino_lookup = load_destino_lookup()
    destino_map = {}
    if not destino_lookup.empty:
        for _, row in destino_lookup.iterrows():
            key = normalize_text(row.get("nombre_destino_norm") or row.get("nombre_destino"))
            if key and key not in destino_map:
                destino_map[key] = row.to_dict()

    points = data.get("points", [])
    if isinstance(points, list):
        for idx, payload in enumerate(points):
            if not isinstance(payload, dict):
                continue
            coords = extract_coordinates(payload)
            dti_norm = normalize_text(payload.get("dti"))
            dest = destino_map.get(dti_norm, {})
            row = {
                "phase": "seguimiento",
                "entity_key": payload.get("uri") or f"point-{idx}",
                "entity_name": payload.get("name") or payload.get("uri") or f"point-{idx}",
                "entity_type": "poi_point",
                "category": strip_accents(payload.get("class")),
                "name": strip_accents(payload.get("name")),
                "class": strip_accents(payload.get("class")),
                "score": as_float(payload.get("score")),
                "razon": strip_accents(payload.get("razon")),
                "lat": coords["latitude"],
                "lon": coords["longitude"],
                "has_coordinates": coords["has_coordinates"],
                "coord_source": coords["coord_source"],
                "dti": strip_accents(payload.get("dti")),
                "dti_norm": dti_norm,
                "uri": strip_accents(payload.get("uri")),
                "range2_out": bool(payload.get("range2_out")) if payload.get("range2_out") is not None else None,
                "destino_nombre": strip_accents(dest.get("nombre_destino")),
                "destino_nombre_norm": strip_accents(dest.get("nombre_destino_norm") or dti_norm),
                "destino_entidad_gestora": strip_accents(dest.get("entidad_gestora")),
                "destino_cif_entidad_gestora": strip_accents(dest.get("cif_entidad_gestora")),
                "destino_comunidad_autonoma": strip_accents(dest.get("comunidad_autonoma")),
                "destino_provincia": strip_accents(dest.get("provincia")),
                "destino_match": bool(dest),
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    if ENABLE_GEOCODING and not df.empty:
        geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT, timeout=15)
        geocode = RateLimiter(
            lambda q: geolocator.geocode(q, addressdetails=True, language="es"),
            min_delay_seconds=GEOCODER_MIN_DELAY_SECONDS,
            max_retries=2,
            swallow_exceptions=True,
        )
        cache: dict[str, dict[str, Any]] = {}
        geocoded_rows: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            if row.get("has_coordinates"):
                geocoded_rows.append(row.to_dict())
                continue
            query_candidates = build_address_candidates(row.to_dict())
            if not query_candidates:
                geocoded_rows.append(row.to_dict())
                continue
            query = query_candidates[0]
            if query not in cache:
                location = geocode(query)
                cache[query] = {
                    "latitude": getattr(location, "latitude", None) if location else None,
                    "longitude": getattr(location, "longitude", None) if location else None,
                    "geocoded": bool(location),
                    "geocode_query": query,
                    "geocode_display_name": getattr(location, "address", None) if location else None,
                }
            geo = cache[query]
            updated = row.to_dict()
            updated["latitude"] = geo.get("latitude")
            updated["longitude"] = geo.get("longitude")
            updated["geocoded"] = geo.get("geocoded", False)
            updated["geocode_query"] = geo.get("geocode_query")
            updated["geocode_display_name"] = geo.get("geocode_display_name")
            geocoded_rows.append(updated)
        df = pd.DataFrame(geocoded_rows)
    return df


def enrich_pois_with_geography(pois: pd.DataFrame, geoms: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if pois.empty:
        return pois

    pois_gdf = gpd.GeoDataFrame(
        pois.copy(),
        geometry=gpd.points_from_xy(pois["lon"], pois["lat"], crs="EPSG:4326"),
    )

    municipios = geoms["municipios"].to_crs(pois_gdf.crs)[
        ["codigo_ine", "nombre_municipio", "codigo_provincia", "nombre_provincia", "codigo_ccaa", "nombre_ccaa", "geometry"]
    ].copy()
    joined = gpd.sjoin(pois_gdf, municipios, how="left", predicate="within")
    if "index_right" in joined.columns:
        joined = joined.drop(columns=["index_right"])

    joined["match_status_geo"] = joined["codigo_ine"].notna().map(lambda x: "matched" if x else "unmatched")

    unmatched_mask = joined["codigo_ine"].isna()
    if unmatched_mask.any():
        pois_proj = pois_gdf.to_crs("EPSG:25830")
        mun_proj = geoms["municipios"].to_crs("EPSG:25830")[
            ["codigo_ine", "nombre_municipio", "codigo_provincia", "nombre_provincia", "codigo_ccaa", "nombre_ccaa", "geometry"]
        ].copy()
        try:
            nearest = gpd.sjoin_nearest(
                pois_proj[unmatched_mask],
                mun_proj,
                how="left",
                max_distance=5000,
                distance_col="distance_m",
            )
            if "index_right" in nearest.columns:
                nearest = nearest.drop(columns=["index_right"])
            for idx, row in nearest.iterrows():
                if pd.notna(row.get("codigo_ine")):
                    for col in ["codigo_ine", "nombre_municipio", "codigo_provincia", "nombre_provincia", "codigo_ccaa", "nombre_ccaa"]:
                        joined.at[idx, col] = row.get(col)
                    joined.at[idx, "match_status_geo"] = "nearest"
        except Exception:
            pass

    joined["codigo_ine"] = joined["codigo_ine"].map(strip_accents)
    joined["nombre_municipio"] = joined["nombre_municipio"].map(strip_accents)
    joined["nombre_provincia"] = joined["nombre_provincia"].map(strip_accents)
    joined["nombre_ccaa"] = joined["nombre_ccaa"].map(strip_accents)
    return pd.DataFrame(joined.drop(columns="geometry"))


def write_json(obj: Any, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def main() -> None:
    ensure_output_dirs()
    geoms = load_geography()
    write_lookup_tables(geoms)

    destinos = normalize_destinos_general()
    modulos = normalize_modulos_comunes()
    turisticos = normalize_datos_turisticos()
    no_ontologicos = normalize_datos_no_ontologicos()
    gestores = normalize_destinos_gestores()
    comarca_ref = build_comarca_reference(destinos, gestores)
    audit_path = find_single_file(["*.json"], must_contain=["audit", "pro"], must_not_contain=["summary"])
    municipio_comarca_detalle, municipio_comarca_resumen = build_municipio_comarca_propuesta(
        audit_path,
        OUTPUT / "geo" / "municipios_lite.csv",
    )
    pois = normalize_json_pois_details()
    pois_geo = enrich_pois_with_geography(pois, geoms)

    destinos.to_csv(OUTPUT / "destinos" / "uso_pid_normalizado.csv", index=False)
    modulos.to_csv(OUTPUT / "destinos" / "modulos_comunes_normalizado.csv", index=False)
    turisticos.to_csv(OUTPUT / "destinos" / "datos_turisticos_normalizado.csv", index=False)
    no_ontologicos.to_csv(OUTPUT / "destinos" / "datos_no_ontologicos_normalizado.csv", index=False)
    gestores.to_csv(OUTPUT / "destinos" / "destinos_gestores_normalizado.csv", index=False)
    comarca_ref.to_csv(OUTPUT / "geo" / "comarcas_lite.csv", index=False)
    municipio_comarca_detalle.to_csv(OUTPUT / "geo" / "municipio_comarca_propuesta.csv", index=False)
    municipio_comarca_resumen.to_csv(OUTPUT / "geo" / "comarcas_propuesta.csv", index=False)
    pois.to_csv(OUTPUT / "pois" / "pois_normalizados.csv", index=False)
    if not pois_geo.empty:
        pois_geo.to_csv(OUTPUT / "pois" / "pois_enriquecidos.csv", index=False)
        pois_geo_gdf = gpd.GeoDataFrame(pois_geo.copy(), geometry=gpd.points_from_xy(pois_geo["lon"], pois_geo["lat"], crs="EPSG:4326"))
        pois_geo_gdf.to_file(OUTPUT / "pois" / "pois_enriquecidos.geojson", driver="GeoJSON")
    if not pois.empty:
        geometry = gpd.points_from_xy(pois["lon"], pois["lat"], crs="EPSG:4326")
        pois_gdf = gpd.GeoDataFrame(pois.copy(), geometry=geometry)
        pois_gdf.to_file(OUTPUT / "pois" / "pois_normalizados.geojson", driver="GeoJSON")
    write_json(summarize_audit_json(), OUTPUT / "pois" / "audit_summary.json")

    manifest = {
        "geography": {
            "municipios": "geo/municipios_lite.geojson",
            "provincias": "geo/provincias_lite.geojson",
            "comunidades_autonomas": "geo/comunidades_autonomas_lite.geojson",
            "comarcas": "geo/comarcas_lite.csv",
            "municipio_comarca_propuesta": "geo/municipio_comarca_propuesta.csv",
            "comarcas_propuesta": "geo/comarcas_propuesta.csv",
        },
        "destinos": {
            "uso_pid": "destinos/uso_pid_normalizado.csv",
            "modulos_comunes": "destinos/modulos_comunes_normalizado.csv",
            "datos_turisticos": "destinos/datos_turisticos_normalizado.csv",
            "datos_no_ontologicos": "destinos/datos_no_ontologicos_normalizado.csv",
            "destinos_gestores": "destinos/destinos_gestores_normalizado.csv",
        },
        "pois": {
            "pois_normalizados": "pois/pois_normalizados.csv",
            "pois_normalizados_geojson": "pois/pois_normalizados.geojson",
            "pois_enriquecidos": "pois/pois_enriquecidos.csv",
            "pois_enriquecidos_geojson": "pois/pois_enriquecidos.geojson",
            "audit_summary": "pois/audit_summary.json",
        },
    }
    write_json(manifest, OUTPUT / "manifest.json")


if __name__ == "__main__":
    main()
