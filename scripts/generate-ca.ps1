# Genera CA (ca.pem, ca-key.pem) para ChirpStack.
# Permite usar "Get Certificate" para gateway y application en la UI.
# Requiere Docker. La clave se genera en PKCS#8 (requerido por ChirpStack).

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ChirpstackConfigDir = Join-Path (Join-Path $ProjectRoot "configuration") "chirpstack"

if (-not (Test-Path $ChirpstackConfigDir)) {
    Write-Error "No existe el directorio: $ChirpstackConfigDir"
    exit 1
}

Write-Host "Generando CA en $ChirpstackConfigDir ..."
$cmd = "apk add --no-cache openssl 2>/dev/null && openssl genpkey -algorithm RSA -out /out/ca-key.pem -pkeyopt rsa_keygen_bits:4096 && openssl req -x509 -new -sha256 -nodes -key /out/ca-key.pem -days 3650 -out /out/ca.pem -subj /CN=ChirpStack_CA"
docker run --rm -v "${ChirpstackConfigDir}:/out" alpine sh -c "$cmd"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error al generar certificados. Comprueba que Docker está en ejecución."
    exit 1
}
Write-Host "OK: ca.pem y ca-key.pem creados en configuration/chirpstack/"
Write-Host "Reinicia ChirpStack para que cargue la CA: docker compose restart chirpstack"
