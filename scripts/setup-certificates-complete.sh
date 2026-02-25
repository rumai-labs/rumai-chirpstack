#!/usr/bin/env sh
# Setup completo de certificados CA para ChirpStack.
# 1. Genera ca.pem y ca-key.pem si no existen.
# 2. Reinicia ChirpStack para cargar la CA.
# Requiere Docker.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CHIRPSTACK_DIR="$PROJECT_ROOT/configuration/chirpstack"
CA_PEM="$CHIRPSTACK_DIR/ca.pem"

if [ ! -d "$CHIRPSTACK_DIR" ]; then
  echo "Error: no existe el directorio $CHIRPSTACK_DIR"
  exit 1
fi

# 1. Generar CA solo si no existe
if [ ! -f "$CA_PEM" ]; then
  echo "[1/2] Generando CA (ca.pem, ca-key.pem) en configuration/chirpstack ..."
  docker run --rm -v "$CHIRPSTACK_DIR:/out" alpine sh -c '
    apk add --no-cache openssl > /dev/null 2>&1
    openssl genpkey -algorithm RSA -out /out/ca-key.pem -pkeyopt rsa_keygen_bits:4096
    openssl req -x509 -new -sha256 -nodes -key /out/ca-key.pem -days 3650 -out /out/ca.pem -subj "/CN=ChirpStack CA"
  '
  echo "      CA creada correctamente."
else
  echo "[1/2] CA ya existe (ca.pem). Omitiendo generación."
fi

# 2. Reiniciar ChirpStack
echo "[2/2] Reiniciando ChirpStack ..."
cd "$PROJECT_ROOT"
docker compose restart chirpstack
echo "      ChirpStack reiniciado."
echo ""
echo "Listo. Ya puedes usar 'Get Certificate' / 'Generate certificate' en la UI"
echo "  - Gateway: en el gateway correspondiente"
echo "  - Application: en Applications -> Integrations -> MQTT"
