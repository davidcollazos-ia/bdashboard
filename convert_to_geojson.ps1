param(
  [string]$InputPath = "C:\Users\dcollazos.SEGITTUR\Documents\ChatGPT\presentacion con datos pid\_repo\audit_PRO_20260710_164731_enriched.json",
  [string]$OutputPath = "C:\Users\dcollazos.SEGITTUR\Documents\ChatGPT\presentacion con datos pid\_repo\audit_PRO_20260710_164731.geojson"
)

function Normalize-Text {
  param([object]$Value)
  if ($null -eq $Value) { return $null }
  $text = [string]$Value
  if ([string]::IsNullOrWhiteSpace($text)) { return $null }
  return $text
}

function Get-FirstNonEmpty {
  param([object[]]$Values)
  foreach ($v in $Values) {
    $t = Normalize-Text $v
    if ($t) { return $t }
  }
  return $null
}

function Infer-Point {
  param([object]$Entity)

  $lat = $Entity.lat
  $lon = $Entity.lon
  $geometrySource = "explicit"

  if ($null -eq $lat -or $null -eq $lon) {
    $geometrySource = "missing"
  }

  if ($null -ne $lat -and $null -ne $lon) {
    return [pscustomobject]@{
      lat = [double]$lat
      lon = [double]$lon
      geometry_source = $geometrySource
    }
  }

  return $null
}

$json = Get-Content -Raw -LiteralPath $InputPath | ConvertFrom-Json
$features = New-Object System.Collections.Generic.List[object]

foreach ($phaseProp in $json.PSObject.Properties) {
  if ($phaseProp.Name -notmatch '^phase\d+$') { continue }
  $phase = $phaseProp.Name
  $phaseNode = $phaseProp.Value
  foreach ($municipalityProp in $phaseNode.PSObject.Properties) {
    $container = $municipalityProp.Value
    $municipality = Normalize-Text $municipalityProp.Name
    $entities = @()
    if ($container -and $container.PSObject.Properties.Name -contains 'entities') {
      $entities = @($container.entities)
    } elseif ($container -is [System.Collections.IEnumerable] -and -not ($container -is [string])) {
      $entities = @($container)
    } else {
      continue
    }

    foreach ($entity in $entities) {
      if ($null -eq $entity) { continue }
      $point = Infer-Point $entity
      $feature = [ordered]@{
        type = 'Feature'
        id = if ($entity.uri) { $entity.uri } else { $null }
        properties = [ordered]@{
          phase = $phase
          municipality = Get-FirstNonEmpty @($entity.municipio, $municipality)
          province = Get-FirstNonEmpty @($entity.provincia, $entity.province)
          name = $entity.name
          clase = $entity.clase
          uri = $entity.uri
          text = $entity.text
          direccion_postal = Get-FirstNonEmpty @($entity.direccion_postal, $entity.address, $entity.postalAddress, $entity.direccion)
        }
      }
      if ($null -ne $point) {
        $feature.geometry = [ordered]@{
          type = 'Point'
          coordinates = @([double]$point.lon, [double]$point.lat)
        }
        $feature.properties.geometry_source = $point.geometry_source
      } else {
        $feature.geometry = $null
        $feature.properties.geometry_source = 'missing'
      }
      $features.Add([pscustomobject]$feature)
    }
  }
}

$geojson = [ordered]@{
  type = 'FeatureCollection'
  features = $features
}

$geojson | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $OutputPath -Encoding utf8
Write-Host "Wrote $OutputPath"
