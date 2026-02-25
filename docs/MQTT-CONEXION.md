# Conectar a MQTT

ChirpStack publica los eventos de dispositivos (uplinks, join, etc.) a un broker MQTT. Puedes **conectarte a ese broker** desde tu aplicación, script o herramienta para recibir datos y enviar downlinks.

---

## 1. Broker que usa ChirpStack (dónde conectarte)

Por defecto ChirpStack publica al **Mosquitto** del mismo Docker Compose:

| Dónde te conectas | Host | Puerto |
|------------------|------|--------|
| Desde tu PC (mismo equipo que Docker) | `localhost` | `1883` |
| Desde otra máquina en la red | IP del servidor donde corre Docker | `1883` |

Sin usuario/contraseña (Mosquitto actual está con `allow_anonymous true`).

---

## 2. Tópicos MQTT (suscribirse y publicar)

### Recibir eventos (suscribirse)

ChirpStack publica en:

```
application/<APPLICATION_ID>/device/<DEV_EUI>/event/<EVENTO>
```

- **APPLICATION_ID**: ID de la aplicación en ChirpStack (lo ves en la UI, no es el JoinEUI).
- **DEV_EUI**: identificador del dispositivo (ej. `0102030405060708`).
- **EVENTO**: tipo de evento.

Eventos típicos:

| Evento | Descripción |
|--------|-------------|
| `up` | Uplink (datos que envía el dispositivo) |
| `join` | Dispositivo hizo join a la red |
| `status` | Estado (margen, batería) |
| `ack` | ACK de downlink confirmado |

**Ejemplos de suscripción** (reemplaza `APPLICATION_ID` por el ID real):

```bash
# Todo lo de una aplicación
mosquitto_sub -h localhost -p 1883 -t "application/APPLICATION_ID/#" -v

# Solo uplinks de esa aplicación
mosquitto_sub -h localhost -p 1883 -t "application/APPLICATION_ID/device/+/event/up" -v

# Un dispositivo concreto
mosquitto_sub -h localhost -p 1883 -t "application/APPLICATION_ID/device/0102030405060708/#" -v
```

Los mensajes vienen en **JSON**.

### Enviar downlink (publicar)

Tópico para programar un downlink:

```
application/<APPLICATION_ID>/device/<DEV_EUI>/command/down
```

Ejemplo de payload (JSON):

```json
{
  "devEui": "0102030405060708",
  "confirmed": false,
  "fPort": 10,
  "data": "AQIDBA=="
}
```

- `data`: payload en **Base64**.
- `confirmed`: `true` si quieres downlink confirmado.

Ejemplo con `mosquitto_pub`:

```bash
mosquitto_pub -h localhost -p 1883 -t "application/APPLICATION_ID/device/0102030405060708/command/down" \
  -m '{"devEui":"0102030405060708","confirmed":false,"fPort":10,"data":"AQIDBA=="}'
```

---

## 3. Usar un broker MQTT externo

Si quieres que ChirpStack publique a **otro broker** (HiveMQ, AWS IoT, broker en la nube, etc.):

1. **Edita** `configuration/chirpstack/chirpstack.toml`:

   ```toml
   [integration.mqtt]
     server="tcp://TU_BROKER:1883/"
     json=true
     username="tu_usuario"      # si el broker lo pide
     password="tu_contraseña"   # si el broker lo pide
   ```

   Para TLS: `server="ssl://TU_BROKER:8883/"` y, si hace falta, configura `ca_cert` en la sección MQTT según la documentación de ChirpStack.

2. **O usa variables de entorno** (recomendado para no guardar secretos en el repo):

   En `docker-compose.yml`, en el servicio `chirpstack`, añade:

   ```yaml
   environment:
     - MQTT_BROKER_HOST=tu-broker.com
     # - MQTT_USERNAME=tu_usuario
     # - MQTT_PASSWORD=tu_contraseña
   ```

   Y en `chirpstack.toml` deja:

   ```toml
   server="tcp://$MQTT_BROKER_HOST:1883/"
   # username="$MQTT_USERNAME"
   # password="$MQTT_PASSWORD"
   ```

3. **Reinicia ChirpStack**: `docker compose restart chirpstack`.

Después, **conéctate tú** al mismo broker (mismo host/puerto/usuario) y suscríbete a los tópicos `application/...` como arriba.

---

## 4. Resumen rápido

| Objetivo | Qué hacer |
|----------|-----------|
| Recibir uplinks/eventos en mi PC | Cliente MQTT a `localhost:1883`, suscribirse a `application/<APP_ID>/device/+/event/up` (o `/#`) |
| Enviar downlink | Publicar en `application/<APP_ID>/device/<DEV_EUI>/command/down` con el JSON de ejemplo |
| Que ChirpStack use otro broker | Cambiar `server` (y opcionalmente `username`/`password`) en `[integration.mqtt]` y reiniciar ChirpStack |

El **APPLICATION_ID** lo ves en la interfaz web de ChirpStack (Applications → tu aplicación → el ID en la URL o en los detalles).
