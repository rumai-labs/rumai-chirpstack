# Cómo hacer lo que pide el proveedor (Hong GPS / Milesight)

El proveedor pide: configurar el gateway, añadir una Application, añadir Data Transmission tipo MQTT con broker, puerto, client ID y tópicos. Depende de **qué tengas tú** (gateway con su interfaz o solo ChirpStack).

---

## ¿Qué tienes?

### A) Tienes un gateway con interfaz web (Milesight/Hong GPS)

Si tienes un **gateway físico** (o una cuenta en la plataforma del proveedor) que tiene su propia interfaz con "Applications" y "Data Transmission":

1. Entra a la **interfaz web del gateway** (la URL que te dio el proveedor).
2. Configura LoRaWAN si te lo piden.
3. Ve a **Applications** → **Add** (o "Añadir aplicación").
4. Dentro de esa aplicación → **Data Transmission** → **Add**.
5. Elige tipo **MQTT** y rellena exactamente:

   | Campo            | Valor |
   |------------------|--------|
   | Broker Address   | `lora.honggps.com` |
   | Broker Port      | `8884` |
   | Client ID        | `mqttx_b3d78c78` |
   | Uplink topic     | `/Filesight/Unplink/<EUI>` (o el patrón que te den; a veces con `$deveui` o `+`) |
   | Downlink topic   | `/Milesight/Downlink/<EUI>` |

6. Guarda. A partir de ahí el gateway usa ese broker y esos tópicos.

**Para enviar downlinks:** desde MQTTX (o cualquier cliente MQTT) conéctate a `lora.honggps.com:8884` (TLS) y publica en `/Milesight/Downlink/<EUI>` el JSON:  
`{"confirmed": true, "fport": 85, "data": "CQEA/w=="}` (ver [DOWNLINK-PROVEEDOR-HONG-GPS.md](DOWNLINK-PROVEEDOR-HONG-GPS.md)).

---

### B) Solo usas ChirpStack (sin esa interfaz del gateway)

ChirpStack **no** tiene "Data Transmission" ni el mismo formulario. Puedes hacer el equivalente y cumplir el objetivo así:

#### 1. Lo que sí haces en ChirpStack (equivalente a “Application”)

- **Applications** → **Add application**.
- Pon nombre (ej. "Dispositivos Milesight").
- Dentro de esa aplicación: **Devices** → añade cada dispositivo (DevEUI, etc.).

Así tienes la “Application” y los dispositivos organizados.

#### 2. “Data Transmission” = enviar/recibir por MQTT del proveedor

ChirpStack no rellena el broker/tópicos del proveedor en un formulario. Para **hacer lo que ellos piden** (usar su MQTT):

- **Recibir uplinks:** si el proveedor publica uplinks en `lora.honggps.com` en tópicos tipo `/Filesight/Unplink/<EUI>`, tú te suscribes a ese broker con un cliente MQTT o con un pequeño programa que, si quieres, reenvíe a ChirpStack (eso ya es integración avanzada).
- **Enviar downlinks:** conéctate al broker del proveedor y publica en el tópico que te pidieron:

  - Broker: `lora.honggps.com`
  - Puerto: `8884` (TLS)
  - Tópico: `/Milesight/Downlink/<EUI_DEL_DISPOSITIVO>`
  - Payload: `{"confirmed": true, "fport": 85, "data": "<base64 del comando>"}`

Eso **es** hacer lo que piden: usar su MQTT para downlinks. No hace falta que ChirpStack tenga un campo “Broker Address / Data Transmission”; lo haces desde fuera (MQTTX, script, o el bridge de abajo).

#### 3. Opcional: que un downlink desde ChirpStack salga también al proveedor

Si quieres enviar el downlink **desde la UI o API de ChirpStack** y que además llegue al broker del proveedor:

- ChirpStack publica en **su** broker (ej. Mosquitto) en  
  `application/<ID>/device/<EUI>/command/down`.
- Un **bridge** (script) se suscribe a ese tópico en ChirpStack, toma el mensaje y lo **republica** en `lora.honggps.com:8884` en `/Milesight/Downlink/<EUI>` con el formato que pide el proveedor.

Así “haces lo que piden” (usar su MQTT para downlinks) y además usas ChirpStack como origen del comando. Ver script `scripts/bridge-downlink-chirpstack-to-provider.py`.

---

## Pasos concretos (solo ChirpStack, sin interfaz del gateway)

1. **En ChirpStack**
   - **Applications** → **Add application** → nombre (ej. "Milesight").
   - Entra a esa aplicación → **Devices** → **Add device** por cada dispositivo (DevEUI, etc.).

2. **Para enviar downlinks al proveedor** (hacer lo que piden con MQTT):
   - Instala un cliente MQTT (ej. [MQTTX](https://mqttx.app/)).
   - Nueva conexión:
     - Host: `lora.honggps.com`
     - Port: `8884`
     - SSL/TLS: **ON**
     - Client ID: `mqttx_b3d78c78`
   - Conectar.
   - Publicar en el tópico `/Milesight/Downlink/<EUI>` (EUI en minúsculas, sin guiones).
   - Payload (JSON): `{"confirmed": true, "fport": 85, "data": "CQEA/w=="}` (o el `data` en Base64 de tu comando).

3. **Opcional:** usar el bridge para que los downlinks que programes en ChirpStack se reenvíen solos al broker del proveedor:
   ```bash
   pip install paho-mqtt
   python scripts/bridge-downlink-chirpstack-to-provider.py
   ```
   (Edita el script con tu broker ChirpStack, broker proveedor y Client ID si cambian.)

---

## Resumen

| Lo que pide el proveedor        | Cómo lo haces |
|--------------------------------|---------------|
| Configurar gateway             | En la **interfaz del gateway** (si la tienes). |
| Añadir Application             | En ChirpStack: **Applications** → Add application. |
| Data Transmission → MQTT       | En ChirpStack no existe ese formulario. Equivalente: usar **el broker del proveedor** (lora.honggps.com:8884) para publicar downlinks en `/Milesight/Downlink/<EUI>`. |
| Broker / Port / Client ID     | Los usas en un **cliente MQTT** (MQTTX, script, o bridge) que se conecta a `lora.honggps.com:8884` con Client ID `mqttx_b3d78c78`. |
| Uplink topic                   | Para recibir uplinks del proveedor: suscribirte a `/Filesight/Unplink/<EUI>` (o el patrón que te den) en ese mismo broker. |
| Downlink topic                 | Para enviar downlinks: publicar en `/Milesight/Downlink/<EUI>`. |

En la práctica: **sí puedes hacer lo que te piden** usando su broker y sus tópicos; si solo tienes ChirpStack, lo haces desde un cliente MQTT o un script/bridge, no desde un formulario “Data Transmission” dentro de ChirpStack.
