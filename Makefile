# Genera CA (ca.pem, ca-key.pem) para certificados de gateway y application en la UI.
# Requiere Docker. Después ejecutar: docker compose restart chirpstack
generate-ca:
	@docker run --rm -v "$$(pwd)/configuration/chirpstack:/out" alpine sh -c '\
		apk add --no-cache openssl > /dev/null 2>&1 && \
		openssl genpkey -algorithm RSA -out /out/ca-key.pem -pkeyopt rsa_keygen_bits:4096 && \
		openssl req -x509 -new -sha256 -nodes -key /out/ca-key.pem -days 3650 -out /out/ca.pem -subj "/CN=ChirpStack CA"'
	@echo "OK: ca.pem y ca-key.pem creados. Reinicia: docker compose restart chirpstack"

# Setup completo: genera CA si no existe y reinicia ChirpStack (un solo comando).
setup-certificates-complete:
	@sh scripts/setup-certificates-complete.sh

import-lorawan-devices:
	docker compose run --rm --entrypoint sh --user root chirpstack -c '\
		apk add --no-cache git && \
		git clone https://github.com/brocaar/lorawan-devices /tmp/lorawan-devices && \
		chirpstack -c /etc/chirpstack import-legacy-lorawan-devices-repository -d /tmp/lorawan-devices'
