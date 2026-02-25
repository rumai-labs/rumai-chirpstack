#!/usr/bin/env sh
# Genera CA (ca.pem, ca-key.pem) para ChirpStack.
# Permite usar "Get Certificate" para gateway y application en la UI.
# Requiere Docker. La clave se genera en PKCS#8 (requerido por ChirpStack).

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CHIRPSTACK_DIR="$PROJECT_ROOT/configuration/chirpstack"

if [ ! -d "$CHIRPSTACK_DIR" ]; then
  echo "Error: no existe el directorio $CHIRPSTACK_DIR"
  exit 1
fi

echo "Generando CA en $CHIRPSTACK_DIR ..."
docker run --rm -v "$CHIRPSTACK_DIR:/out" alpine sh -c '
  apk add --no-cache openssl > /dev/null 2>&1
  openssl genpkey -algorithm RSA -out /out/ca-key.pem -pkeyopt rsa_keygen_bits:4096
  openssl req -x509 -new -sha256 -nodes -key /out/ca-key.pem -days 3650 -out /out/ca.pem -subj "/CN=ChirpStack CA"
'
echo "OK: ca.pem y ca-key.pem creados en configuration/chirpstack/"
echo "Reinicia ChirpStack para que cargue la CA: docker compose restart chirpstack"
