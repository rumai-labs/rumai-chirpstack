#!/usr/bin/env python3
"""
Bridge: escucha downlinks en el broker de ChirpStack (Mosquitto) y los
republica en el broker del proveedor en /Milesight/Downlink/<devEui>.

Configuración por variables de entorno (o valores por defecto).
En Docker Compose se inyectan desde el servicio mqtt-bridge-provider.
"""

import json
import logging
import os
import ssl
import sys
import time
import warnings

# Evitar DeprecationWarning de paho-mqtt 2.x (Callback API VERSION1)
warnings.filterwarnings("ignore", message=".*Callback API version 1 is deprecated.*", category=DeprecationWarning)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Instala paho-mqtt: pip install paho-mqtt", flush=True)
    sys.exit(1)

# Logs a stdout para verse en docker compose logs
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)


def env(key, default):
    return os.environ.get(key, default)


def env_int(key, default):
    v = env(key, str(default))
    return int(v) if v else int(default)


# --- ChirpStack (Mosquitto) ---
CHIRPSTACK_BROKER = env("CHIRPSTACK_MQTT_HOST", "localhost")
CHIRPSTACK_PORT = env_int("CHIRPSTACK_MQTT_PORT", 1883)
CHIRPSTACK_USE_TLS = env("CHIRPSTACK_MQTT_TLS", "false").lower() in ("1", "true", "yes")

# --- Proveedor (Hong GPS / Milesight) ---
PROVIDER_BROKER = env("PROVIDER_MQTT_HOST", "lora.honggps.com")
PROVIDER_PORT = env_int("PROVIDER_MQTT_PORT", 8884)
PROVIDER_USE_TLS = env("PROVIDER_MQTT_TLS", "true").lower() in ("1", "true", "yes")
# Puerto 8884 suele ser MQTT sobre WebSockets (wss). Si falla TLS con "Unexpected EOF", probar websockets.
PROVIDER_USE_WEBSOCKETS = env("PROVIDER_MQTT_WEBSOCKETS", "true").lower() in ("1", "true", "yes")
PROVIDER_CLIENT_ID = env("PROVIDER_MQTT_CLIENT_ID", "mqttx_b3d78c78")
PROVIDER_DOWNLINK_TOPIC = env("PROVIDER_DOWNLINK_TOPIC", "/Milesight/Downlink/{}")
PROVIDER_CONNECT_RETRY_SEC = env_int("PROVIDER_CONNECT_RETRY_SEC", 30)
# Si true, si no se puede conectar al proveedor el bridge igual arranca y solo registra downlinks (no reenvía)
PROVIDER_OPTIONAL = env("PROVIDER_OPTIONAL", "false").lower() in ("1", "true", "yes")
# Si true, prueba varios puertos/tipos habituales (8884 TLS, 8884 WSS, 8883 TLS, 1883 sin TLS) hasta que uno conecte
PROVIDER_TRY_ALL_PORTS = env("PROVIDER_TRY_ALL_PORTS", "true").lower() in ("1", "true", "yes")

# Candidatos para autodetección: (puerto, tls, websockets). Se prueba en orden hasta que uno conecte.
PROVIDER_CANDIDATES = [
    (8884, True, False),   # 8884 MQTT sobre TLS
    (8884, True, True),    # 8884 WSS
    (8883, True, False),   # 8883 MQTT TLS (estándar IANA)
    (1883, False, False),  # 1883 MQTT sin TLS (estándar)
    (8084, False, True),   # 8084 MQTT WebSocket sin TLS (ws) - ej. ThingsBoard
    (8084, True, True),    # 8084 MQTT WebSocket + TLS (wss)
    (8083, True, False),   # 8083 TLS (algunos brokers)
    (8083, False, False), # 8083 sin TLS
    (8080, False, True),  # 8080 WebSocket (ws)
    (8080, True, True),   # 8080 WSS
    (443, True, True),     # 443 WSS (común en cloud)
]


def _try_connect_provider(callback_api, host, port, use_tls, use_websockets, client_id, timeout_sec=10):
    """Intenta conectar al proveedor con la config dada. Devuelve el Client conectado o None."""
    transport = "websockets" if use_websockets else "tcp"
    if callback_api is not None:
        args = [callback_api.VERSION1, client_id]
    else:
        args = [client_id]
    client = mqtt.Client(*args, protocol=mqtt.MQTTv311, transport=transport)
    if use_tls:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            if hasattr(ssl, "TLSVersion"):
                ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            client.tls_set_context(ctx)
        except AttributeError:
            client.tls_set(cert_reqs=ssl.CERT_NONE)
    try:
        client.connect(host, port, 60)
        return client
    except Exception:
        try:
            client.disconnect()
        except Exception:
            pass
        return None


def on_connect_chirpstack(client, userdata, flags, rc):
    if rc != 0:
        log.error("ChirpStack: conexión fallida rc=%s", rc)
        return
    log.info("ChirpStack: conectado. Suscribiendo a application/+/device/+/command/down")
    client.subscribe("application/+/device/+/command/down", qos=1)


def on_message_chirpstack(client, userdata, msg):
    if log.isEnabledFor(logging.DEBUG):
        payload_preview = (msg.payload[:200] if msg.payload else b"") or b""
        log.debug("Mensaje recibido topic=%s payload=%s", msg.topic, payload_preview)
    try:
        payload = json.loads(msg.payload.decode())
    except Exception as e:
        log.warning("Payload no JSON: %s", e)
        return
    dev_eui = payload.get("devEui") or payload.get("dev_eui")
    if not dev_eui:
        log.warning("Mensaje sin devEui, ignorado. Tópico=%s", msg.topic)
        return
    # Normalizar EUI a minúsculas sin separadores (ChirpStack puede enviar string o hex)
    dev_eui = str(dev_eui).lower().replace("-", "").replace(":", "")
    # Formato que pide el proveedor
    out = {
        "confirmed": payload.get("confirmed", True),
        "fport": payload.get("fPort") or payload.get("fport", 85),
        "data": payload.get("data", ""),
    }
    topic = (PROVIDER_DOWNLINK_TOPIC or "/Milesight/Downlink/{}").format(dev_eui)
    provider_client = userdata.get("provider_client")
    if provider_client is None:
        log.info("Downlink recibido (proveedor no conectado) | devEui=%s | fport=%s | data_len=%s",
                 dev_eui, out["fport"], len(out.get("data", "")))
        return
    try:
        provider_client.publish(topic, json.dumps(out), qos=1)
        log.info("Downlink reenviado a proveedor | topic=%s | devEui=%s | fport=%s", topic, dev_eui, out["fport"])
    except Exception as e:
        log.error("Error al publicar en proveedor topic=%s: %s", topic, e)


def main():
    log.info("=== MQTT bridge ChirpStack -> Proveedor iniciando ===")
    log.info("ChirpStack: %s:%s | Proveedor: %s", CHIRPSTACK_BROKER, CHIRPSTACK_PORT, PROVIDER_BROKER)

    callback_api = getattr(mqtt, "CallbackAPIVersion", None)
    if callback_api is not None:
        chirpstack_client_args = [callback_api.VERSION1]
    else:
        chirpstack_client_args = []

    provider = None
    if PROVIDER_TRY_ALL_PORTS:
        log.info("Probando puertos/tipos: 8884, 8883, 1883, 8084, 8083, 8080, 443 (TLS/WSS/ws)...")
        for port, use_tls, use_ws in PROVIDER_CANDIDATES:
            kind = f"{port} TLS" if use_tls and not use_ws else f"{port} WSS" if use_ws else f"{port} sin TLS"
            log.info("Intentando %s %s ...", PROVIDER_BROKER, kind)
            provider = _try_connect_provider(
                callback_api, PROVIDER_BROKER, port, use_tls, use_ws, PROVIDER_CLIENT_ID
            )
            if provider is not None:
                log.info("Conectado al proveedor en %s", kind)
                break
        if provider is None:
            log.warning("Ninguna combinación puerto/tipo funcionó")
    else:
        transport = "websockets" if PROVIDER_USE_WEBSOCKETS else "tcp"
        if callback_api is not None:
            provider_client_args = [callback_api.VERSION1, PROVIDER_CLIENT_ID]
        else:
            provider_client_args = [PROVIDER_CLIENT_ID]
        provider = mqtt.Client(*provider_client_args, protocol=mqtt.MQTTv311, transport=transport)
        if PROVIDER_USE_TLS:
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                if hasattr(ssl, "TLSVersion"):
                    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                provider.tls_set_context(ctx)
            except AttributeError:
                provider.tls_set(cert_reqs=ssl.CERT_NONE)
        while True:
            try:
                log.info("Conectando al proveedor %s:%s ...", PROVIDER_BROKER, PROVIDER_PORT)
                provider.connect(PROVIDER_BROKER, PROVIDER_PORT, 60)
                log.info("Conectado al proveedor correctamente")
                break
            except Exception as e:
                log.warning("No se pudo conectar al proveedor %s:%s: %s", PROVIDER_BROKER, PROVIDER_PORT, e)
                if PROVIDER_OPTIONAL:
                    log.info("PROVIDER_OPTIONAL=true: siguiendo sin proveedor (solo se registrarán downlinks)")
                    provider = None
                    break
                log.info("Reintento en %ss ...", PROVIDER_CONNECT_RETRY_SEC)
                time.sleep(PROVIDER_CONNECT_RETRY_SEC)

    if provider is None:
        if not PROVIDER_OPTIONAL and not PROVIDER_TRY_ALL_PORTS:
            log.error("No se pudo conectar al proveedor. Configure PROVIDER_OPTIONAL=true o pruebe otro puerto.")
            sys.exit(1)
        log.info("Proveedor no conectado. Siguiendo solo con ChirpStack (downlinks se registrarán, no se reenviarán)")

    # Cliente hacia ChirpStack (Mosquitto)
    chirpstack = mqtt.Client(*chirpstack_client_args, protocol=mqtt.MQTTv311)
    chirpstack.user_data_set({"provider_client": provider})
    chirpstack.on_connect = on_connect_chirpstack
    chirpstack.on_message = on_message_chirpstack
    while True:
        try:
            log.info("Conectando a ChirpStack (Mosquitto) %s:%s ...", CHIRPSTACK_BROKER, CHIRPSTACK_PORT)
            chirpstack.connect(CHIRPSTACK_BROKER, CHIRPSTACK_PORT, 60)
            break
        except Exception as e:
            log.warning("No se pudo conectar a ChirpStack %s:%s: %s", CHIRPSTACK_BROKER, CHIRPSTACK_PORT, e)
            log.info("Reintento en %ss ...", PROVIDER_CONNECT_RETRY_SEC)
            time.sleep(PROVIDER_CONNECT_RETRY_SEC)

    chirpstack.loop_start()
    if provider is not None:
        provider.loop_start()
    log.info("Bridge en ejecución. Esperando downlinks de ChirpStack (application/+/device/+/command/down)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Salida por Ctrl+C")
    chirpstack.loop_stop()
    if provider is not None:
        provider.loop_stop()


if __name__ == "__main__":
    main()
