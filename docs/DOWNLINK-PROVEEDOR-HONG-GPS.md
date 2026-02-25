# Downlinks con el broker del proveedor (Hong GPS / Milesight)

Configuración indicada por tu proveedor para enviar downlinks por MQTT.

---

## 1. Datos del broker (proveedor)

| Parámetro    | Valor              |
|-------------|--------------------|
| **Broker**  | `lora.honggps.com` |
| **Puerto**  | `8884` (MQTT sobre TLS) |
| **Client ID** | `mqttx_b3d78c78` |

### Tópicos

| Tipo     | Tópico |
|----------|--------|
| **Uplink** (datos que envía el dispositivo) | `/Filesight/Unplink/<EUI_DEL_DISPOSITIVO>` |
| **Downlink** (comandos que tú envías al dispositivo) | `/Milesight/Downlink/<EUI_DEL_DISPOSITIVO>` |

Sustituye `<EUI_DEL_DISPOSITIVO>` por el EUI real, por ejemplo: `24e124126a148401` (minúsculas, sin separadores).

---

## 2. Dónde configurar esto

Tu proveedor dice:

1. **Interfaz del gateway** → Configurar parámetros LoRaWAN.
2. **Applications** (en esa interfaz) → Añadir una aplicación.
3. En esa aplicación → **Data Transmission** → Añadir una.
4. Tipo: **MQTT**.
5. Rellenar:
   - **Broker Address:** `lora.honggps.com`
   - **Broker Port:** `8884`
   - **Client ID:** `mqttx_b3d78c78`
   - **Uplink topic:** `/Filesight/Unplink/<EUI>` (o el patrón que te den)
   - **Downlink topic:** `/Milesight/Downlink/<EUI>`

Eso se hace en la **interfaz web del gateway** (o de la plataforma Hong GPS / Milesight), no en ChirpStack.

---

## 3. Cómo enviar un downlink por MQTT

Para **enviar tú** un downlink al dispositivo:

1. Conectarte al broker **lora.honggps.com:8884** (TLS).
2. Publicar en el tópico:
   ```
   /Milesight/Downlink/<EUI_DEL_DISPOSITIVO>
   ```
3. Payload en **JSON** (formato estándar Milesight):

   ```json
   {
     "confirmed": true,
     "fport": 85,
     "data": "CQEA/w=="
   }
   ```

   - **confirmed:** `true` = el dispositivo debe confirmar; `false` = envío no confirmado.
   - **fport:** puerto de aplicación (85 es el habitual en dispositivos Milesight).
   - **data:** comando en **Base64**. El contenido real del comando suele ir en hexadecimal; se convierte a Base64 para este campo.

### Ejemplo de comando (Base64)

- Comando típico de ejemplo: hex `090100ff` → Base64 `CQEA/w==`.
- Para otros comandos del dispositivo, revisa la documentación del modelo (Milesight) y convierte el hex a Base64 (por ejemplo en https://tomeko.net/online_tools/hex_to_base64.php).

---

## 4. Enviar downlink con MQTTX (o similar)

1. Abre **MQTTX** (o MQTT Explorer).
2. Nueva conexión:
   - **Host:** `lora.honggps.com`
   - **Port:** `8884`
   - **SSL/TLS:** activado (puerto 8884 suele ser MQTT over TLS).
   - **Client ID:** `mqttx_b3d78c78` (o el que te haya dado el proveedor).
   - Usuario/contraseña solo si el proveedor te los ha dado.
3. Conectar.
4. Publicar:
   - **Topic:** `/Milesight/Downlink/24e124126a148401` (cambia por el EUI de tu dispositivo).
   - **Payload:** JSON anterior, por ejemplo:
     ```json
     {"confirmed": true, "fport": 85, "data": "CQEA/w=="}
     ```

Si el gateway (o la nube del proveedor) está bien configurado y suscrito a ese tópico, recibirá el mensaje y lo enviará por LoRaWAN al dispositivo.

---

## 5. Enviar downlink con Python (ejemplo)

```python
import ssl
import json
import paho.mqtt.client as mqtt

BROKER = "lora.honggps.com"
PORT = 8884
CLIENT_ID = "mqttx_b3d78c78"
DEV_EUI = "24e124126a148401"  # Reemplaza por el EUI de tu dispositivo
TOPIC = f"/Milesight/Downlink/{DEV_EUI}"

payload = {
    "confirmed": True,
    "fport": 85,
    "data": "CQEA/w=="   # Base64 del comando hex (ej. 090100ff)
}

client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
client.tls_set(cert_reqs=ssl.CERT_NONE)  # Ajusta si el broker usa certificados
client.connect(BROKER, PORT, 60)
client.publish(TOPIC, json.dumps(payload), qos=1)
client.disconnect()
print("Downlink enviado a", TOPIC)
```

Instalar: `pip install paho-mqtt`. Si el broker pide usuario/contraseña, usa `client.username_pw_set("user", "pass")` antes de `connect`.

---

## 6. Resumen

| Qué quieres hacer | Dónde / cómo |
|-------------------|---------------|
| Configurar broker y tópicos en el gateway | Interfaz del gateway (Hong GPS / Milesight) → Applications → Data Transmission → MQTT |
| Enviar un downlink manualmente | Cliente MQTT a `lora.honggps.com:8884` (TLS), publicar en `/Milesight/Downlink/<EUI>` con el JSON de arriba |
| Ver uplinks del dispositivo | Suscribirse a `/Filesight/Unplink/<EUI>` (o al patrón que indique el proveedor) en el mismo broker |

Si el proveedor te da **usuario/contraseña** o **certificados** para el puerto 8884, configúralos en el cliente MQTT (MQTTX, Python, etc.).

### Error "SSL: UNEXPECTED_EOF_WHILE_READING" al conectar

Si al conectar a `lora.honggps.com:8884` aparece ese error (sobre todo desde Docker), prueba:

1. **Otro puerto:** Muchos brokers usan **8883** para MQTT sobre TLS (no 8884). En el compose: `PROVIDER_MQTT_PORT=8883`.
2. **Sin TLS:** Si el proveedor tiene MQTT en **1883** sin cifrado: `PROVIDER_MQTT_PORT=1883` y `PROVIDER_MQTT_TLS=false`.
3. **Confirmar con el proveedor:** Que 8884 sea el puerto correcto, si es TLS o WebSockets, y si hace falta usuario/contraseña o certificados cliente.
4. **Bridge sin proveedor:** Con `PROVIDER_OPTIONAL=true` el bridge arranca aunque no se conecte al proveedor; los downlinks se registran en log y podés seguir usando ChirpStack.
