# Setup completo de certificados CA para ChirpStack.
# 1. Genera ca.pem y ca-key.pem si no existen.
# 2. Reinicia ChirpStack para cargar la CA.
# Así puedes usar "Get Certificate" para gateway y application en la UI.
# Requiere Docker en ejecución.

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ChirpstackConfigDir = Join-Path (Join-Path $ProjectRoot "configuration") "chirpstack"
$CaPem = Join-Path $ChirpstackConfigDir "ca.pem"

if (-not (Test-Path $ChirpstackConfigDir)) {
    Write-Error "No existe el directorio: $ChirpstackConfigDir"
    exit 1
}

# 1. Generar CA solo si no existe
if (-not (Test-Path $CaPem)) {
    Write-Host "[1/2] Generando CA (ca.pem, ca-key.pem) en configuration/chirpstack ..."
    $cmd = "apk add --no-cache openssl 2>/dev/null && openssl genpkey -algorithm RSA -out /out/ca-key.pem -pkeyopt rsa_keygen_bits:4096 && openssl req -x509 -new -sha256 -nodes -key /out/ca-key.pem -days 3650 -out /out/ca.pem -subj /CN=ChirpStack_CA"
    docker run --rm -v "${ChirpstackConfigDir}:/out" alpine sh -c "$cmd"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error al generar certificados. Comprueba que Docker está en ejecución."
        exit 1
    }
    Write-Host "      CA creada correctamente."
} else {
    Write-Host "[1/2] CA ya existe (ca.pem). Omitiendo generación."
}

# 2. Reiniciar ChirpStack para que cargue la CA
Write-Host "[2/2] Reiniciando ChirpStack ..."
Set-Location $ProjectRoot
docker compose restart chirpstack
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error al reiniciar ChirpStack."
    exit 1
}
Write-Host "      ChirpStack reiniciado."
Write-Host ""
Write-Host "Listo. Ya puedes usar 'Get Certificate' / 'Generate certificate' en la UI"
Write-Host "  - Gateway: en el gateway correspondiente"
Write-Host "  - Application: en Applications -> Integrations -> MQTT"
