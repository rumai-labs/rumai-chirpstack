# Cómo son las Applications y MQTT en ChirpStack

En ChirpStack no existe "Data Transmission" como en el gateway del proveedor. La estructura es otra.

---

## Estructura en ChirpStack

```
ChirpStack
└── Applications (lista de aplicaciones)
    └── [Cada aplicación]
        ├── Devices          ← dispositivos (DevEUI, etc.)
        ├── Integrations     ← aquí está MQTT (y HTTP, etc.)
        ├── Payload codecs
        └── ...
```

- **Applications**: son las "apps" o proyectos (ej. "Sensores campo", "Tracking").
- **Devices**: cada dispositivo LoRaWAN pertenece a **una** aplicación.
- **Integrations**: por aplicación puedes activar **integraciones** (MQTT, HTTP…) para enviar eventos y recibir downlinks. Ahí se configura/usa MQTT.

No hay un paso tipo "añadir Data Transmission" como en el gateway Milesight; en ChirpStack el equivalente es **crear una Application** y luego usar **Integrations** (por ejemplo MQTT).

---

## Dónde se ve en la interfaz

1. **Menú lateral** → **Applications**  
   Ahí ves la lista de aplicaciones (apps).

2. **Entrar a una aplicación**  
   Clic en el nombre de la aplicación.

3. **Dentro de la aplicación** tienes pestañas/secciones como:
   - **Devices** – lista de dispositivos de esa aplicación.
   - **Integrations** – integraciones (MQTT, HTTP, etc.).
   - **Payload codecs**, etc.

4. **Integrations**  
   Ahí se configura o se usa MQTT para esa aplicación (eventos que ChirpStack publica y tópicos para downlink).

---

## Cómo se relaciona con el broker (MQTT)

- ChirpStack tiene **un** broker MQTT global (en `chirpstack.toml`, ej. Mosquitto en 1883).
- Para **cada aplicación**, ChirpStack publica en tópicos:
  - `application/<APPLICATION_ID>/device/<DEV_EUI>/event/up` (uplinks)
  - y tú envías downlinks a:
  - `application/<APPLICATION_ID>/device/<DEV_EUI>/command/down`

El **APPLICATION_ID** es un ID interno de ChirpStack (número o UUID), no el nombre que le pusiste a la app. Lo ves en la URL cuando entras a la aplicación o en la API.

---

## Resumen rápido

| En el gateway del proveedor | En ChirpStack |
|----------------------------|----------------|
| "Applications"             | **Applications** (menú lateral) |
| "Data Transmission" → MQTT | **Integrations** (dentro de cada Application) → MQTT |
| Configurar broker/tópicos  | Broker global en `chirpstack.toml`; tópicos son `application/<ID>/device/<EUI>/...` |

Si quieres usar el broker del proveedor (lora.honggps.com:8884) con los tópicos `/Milesight/Downlink/...`, eso es **aparte** de ChirpStack: se hace con un cliente MQTT o tu backend publicando a ese broker, como en [DOWNLINK-PROVEEDOR-HONG-GPS.md](DOWNLINK-PROVEEDOR-HONG-GPS.md). ChirpStack por defecto usa su propio broker (ej. Mosquitto) y los tópicos `application/...`.
